# Copyright 2019 The Bazel Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""To be executed on each docker container that runs the tasks.

Clones the repository and downloads available bazel binaries.

"""
import argparse
import bazelci
import os
import sys


BB_ROOT = os.path.join(os.path.expanduser("~"), ".bazel-bench")
# The path to the directory that stores the bazel binaries.
BAZEL_BINARY_BASE_PATH = os.path.join(BB_ROOT, "bazel-bin")


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Bazel Bench Environment Setup")
    parser.add_argument("--platform", type=str)
    parser.add_argument("--bazel_commits", type=str)
    args = parser.parse_args(argv)

    bazel_commits = args.bazel_commits.split(",")
    # We use one binary for all Linux platforms.
    # Context: https://github.com/bazelbuild/continuous-integration/blob/master/buildkite/bazelci.py
    binary_platform = (
        args.platform if args.platform in ["macos", "windows"] else bazelci.LINUX_BINARY_PLATFORM
    )
    bazel_bin_dir = BAZEL_BINARY_BASE_PATH + "/" + binary_platform

    for bazel_commit in bazel_commits:
        destination = bazel_bin_dir + "/" + bazel_commit
        if os.path.exists(destination):
            continue
        try:
            bazelci.download_bazel_binary_at_commit(destination, binary_platform, bazel_commit)
        except bazelci.BuildkiteException:
            # Carry on.
            bazelci.eprint("Binary for Bazel commit %s not found." % bazel_commit)


if __name__ == "__main__":
    sys.exit(main())
