#!/usr/bin/env python3
#
# Copyright 2021 The Bazel Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import collections
import os
import subprocess
import sys

import bazelci

DEFAULT_FLAGS = ["--action_env=PATH=/usr/local/bin:/usr/bin:/bin", "--sandbox_tmpfs_path=/tmp"]

Settings = collections.namedtuple(
    "Settings", ["target", "build_flags", "output_dir", "gcs_bucket", "gcs_subdir", "landing_page"]
)

DOCGEN_SETTINGS = {
    "bazel-trusted": {
        "https://github.com/bazelbuild/bazel.git": Settings(
            target="//site",
            build_flags=[],
            output_dir="bazel-bin/site/site-build",
            gcs_bucket="docs.bazel.build",
            gcs_subdir="",
            landing_page="versions/master/bazel-overview.html",
        ),
        "https://github.com/bazelbuild/bazel-blog.git": Settings(
            target="//:site",
            build_flags=[],
            output_dir="bazel-bin/site-build",
            gcs_bucket="blog.bazel.build",
            gcs_subdir="",
            landing_page="index.html",
        ),
        "https://github.com/bazelbuild/bazel-website.git": Settings(
            target="//:site",
            build_flags=[],
            output_dir="bazel-bin/site-build",
            gcs_bucket="www.bazel.build",
            gcs_subdir="",
            landing_page="index.html",
        ),
    },
}


def get_destination(bucket, subdir):
    if not subdir:
        return bucket

    return "{}/{}".format(bucket, subdir)


def get_url(settings):
    return "https://{}/{}".format(
        get_destination(settings.gcs_bucket, settings.gcs_subdir), settings.landing_page
    )


def main(argv=None):
    org = os.getenv("BUILDKITE_ORGANIZATION_SLUG")
    repo = os.getenv("BUILDKITE_REPO")
    settings = DOCGEN_SETTINGS.get(org, {}).get(repo)
    if not settings:
        bazelci.eprint("docgen is not enabled for '%s' org and repository %s", org, repo)
        return 1

    bazelci.print_expanded_group(":bazel: Building documentation from {}".format(repo))
    try:
        bazelci.execute_command(
            ["bazel", "build"] + DEFAULT_FLAGS + settings.build_flags + [settings.target]
        )
    except subprocess.CalledProcessError as e:
        bazelci.eprint("Bazel failed with exit code {}".format(e.returncode))
        return e.returncode

    bucket = "gs://{}".format(settings.gcs_bucket)
    dest = get_destination(bucket, settings.gcs_subdir)
    bazelci.print_expanded_group(":bazel: Uploading documentation to {}".format(dest))
    try:
        bazelci.execute_command(
            ["gsutil", "-m", "rsync", "-r", "-c", "-d", settings.output_dir, dest]
        )
        bazelci.execute_command(
            ["gsutil", "web", "set", "-m", "index.html", "-e", "404.html", bucket]
        )
        # TODO: does not work with 404 pages in sub directories
    except subprocess.CalledProcessError as e:
        bazelci.eprint("Upload to GCS failed with exit code {}".format(e.returncode))
        return e.returncode

    bazelci.print_collapsed_group(":bazel: Publishing documentation URL")
    message = "You can find the documentation at {}".format(get_url(settings))
    bazelci.execute_command(
        ["buildkite-agent", "annotate", "--style=info", message, "--context", "doc_url"]
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
