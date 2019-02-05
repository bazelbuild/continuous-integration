#!/usr/bin/env python3
#
# Copyright 2019 The Bazel Authors. All rights reserved.
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

import os
import subprocess

from config import CLOUD_PROJECT
from utils import gsutil_command, execute_command, eprint


def bazelci_last_green_commit_url(git_repository, pipeline_slug):
    return "gs://%s/last_green_commit/%s/%s" % (
        "bazel-builds" if CLOUD_PROJECT == "bazel-public" else "bazel-untrusted-builds",
        git_repository[len("https://") :],
        pipeline_slug,
    )


def get_last_green_commit(git_repository, pipeline_slug):
    last_green_commit_url = bazelci_last_green_commit_url(git_repository, pipeline_slug)
    try:
        return (
            subprocess.check_output(
                [gsutil_command(), "cat", last_green_commit_url], env=os.environ
            )
            .decode("utf-8")
            .strip()
        )
    except subprocess.CalledProcessError:
        return None


def main():
    pipeline_slug = os.getenv("BUILDKITE_PIPELINE_SLUG")
    git_repository = os.getenv("BUILDKITE_REPO")
    last_green_commit = get_last_green_commit(git_repository, pipeline_slug)
    current_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    if last_green_commit:
        execute_command(["git", "fetch", "-v", "origin", last_green_commit])
        result = (
            subprocess.check_output(
                ["git", "rev-list", "%s..%s" % (last_green_commit, current_commit)]
            )
            .decode("utf-8")
            .strip()
        )

    # If current_commit is newer that last_green_commit, `git rev-list A..B` will output a bunch of
    # commits, otherwise the output should be empty.
    if not last_green_commit or result:
        execute_command(
            [
                "echo %s | %s cp - %s"
                % (
                    current_commit,
                    gsutil_command(),
                    bazelci_last_green_commit_url(git_repository, pipeline_slug),
                )
            ],
            shell=True,
        )
    else:
        eprint(
            "Updating abandoned: last green commit (%s) is not older than current commit (%s)."
            % (last_green_commit, current_commit)
        )
