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
import shutil
import subprocess
import sys
import tempfile

import bazelci

DEFAULT_FLAGS = ["--action_env=PATH=/usr/local/bin:/usr/bin:/bin", "--sandbox_tmpfs_path=/tmp"]

PLATFORM = "ubuntu1804"

Settings = collections.namedtuple(
    "Settings",
    ["target", "build_flags", "output_dir", "gcs_bucket", "gcs_subdir", "landing_page", "rewrite"],
)

BUILDKITE_BUILD_NUMBER = os.getenv("BUILDKITE_BUILD_NUMBER")


DOCGEN_SETTINGS = {
    "bazel-trusted": {
        "https://github.com/bazelbuild/bazel-blog.git": Settings(
            target="//:site",
            build_flags=[],
            output_dir="bazel-bin/site-build",
            gcs_bucket="blog.bazel.build",
            gcs_subdir="",
            landing_page="index.html",
            rewrite=None,
        ),
    },
}


def rewrite_and_copy(src_root, dest_root, rewrite):
    for src_dir, dirs, files in os.walk(src_root):
        dest_dir = src_dir.replace(src_root, dest_root, 1)
        os.mkdir(dest_dir)

        for filename in files:
            src_file = os.path.join(src_dir, filename)
            dest_file = os.path.join(dest_dir, filename)

            if src_file.endswith(".html"):
                with open(src_file, "r", encoding="utf-8") as src:
                    content = src.read()

                with open(dest_file, "w", encoding="utf-8") as dest:
                    dest.write(rewrite(content))
            else:
                shutil.copyfile(src_file, dest_file)


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

    src_root = os.path.join(os.getcwd(), settings.output_dir)
    if settings.rewrite:
        bazelci.print_expanded_group(":bazel: Rewriting links in documentation files")
        dest_root = os.path.join(tempfile.mkdtemp(), "site")
        rewrite_and_copy(src_root, dest_root, settings.rewrite)
        src_root = dest_root

    bucket = "gs://{}".format(settings.gcs_bucket)
    dest = get_destination(bucket, settings.gcs_subdir)
    bazelci.print_expanded_group(":bazel: Uploading documentation to {}".format(dest))
    try:
        bazelci.execute_command(["gsutil", "-m", "rsync", "-r", "-c", "-d", src_root, dest])
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
    bazelci.execute_command(["buildkite-agent", "meta-data", "set", "message", message])

    return 0


if __name__ == "__main__":
    sys.exit(main())
