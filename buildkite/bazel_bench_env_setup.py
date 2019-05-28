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
import tempfile

def _platform_path_str(posix_path):
  """Converts the path to the appropriate format for platform."""
  if os.name == "nt":
    return posix_path.replace("/", "\\")
  return posix_path


# TODO(leba): Make these configurable via flags to the script.
# TMP has different values, depending on the platform.
TMP = tempfile.gettempdir()
# The path to the directory that stores the bazel binaries.
BAZEL_BINARY_BASE_PATH = _platform_path_str("%s/.bazel-bench/bazel-bin" % TMP)

def main(argv=None):
  if argv is None:
    argv = sys.argv[1:]

  parser = argparse.ArgumentParser(description="Bazel Bench Environment Setup")
  parser.add_argument("--platform", type=str)
  parser.add_argument("--bazel_commits", type=str)
  args = parser.parse_args(argv)

  bazel_commits = args.bazel_commits.split(",")

  for bazel_commit in bazel_commits:
    destination = BAZEL_BINARY_BASE_PATH + '/' + bazel_commit
    if os.path.exists(destination):
      continue

    bazelci.download_bazel_binary_at_commit(
      destination,
      platform,
      bazel_commit
    )


if __name__ == "__main__":
  sys.exit(main())
