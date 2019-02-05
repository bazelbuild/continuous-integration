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
import sys
import stat
import time

from config import PLATFORMS


def print_collapsed_group(name):
    eprint("\n\n--- {0}\n\n".format(name))


def print_expanded_group(name):
    eprint("\n\n+++ {0}\n\n".format(name))


def python_binary(platform=None):
    if platform == "windows":
        return "python.exe"
    if platform == "macos":
        return "python3.7"
    return "python3.6"


def bazelci_builds_gs_url(platform, git_commit):
    return "gs://bazel-builds/artifacts/{0}/{1}/bazel".format(platform, git_commit)


def bazelcipy_url():
    """
    URL to the latest version of this script.
    """
    return "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?{}".format(
        int(time.time())
    )


def gcloud_command():
    return "gcloud.cmd" if is_windows() else "gcloud"


def fetch_bazelcipy_command():
    return "curl -sS {0} -o bazelci.py".format(bazelcipy_url())


def eprint(*args, **kwargs):
    print(*args, flush=True, file=sys.stderr, **kwargs)


def is_windows():
    return os.name == "nt"


def gsutil_command():
    return "gsutil.cmd" if is_windows() else "gsutil"


def create_label(platform, project_name, build_only=False, test_only=False):
    if build_only and test_only:
        raise Exception("build_only and test_only cannot be true at the same time")
    platform_name = PLATFORMS[platform]["emoji-name"]

    if build_only:
        label = "Build "
    elif test_only:
        label = "Test "
    else:
        label = ""

    if project_name:
        label += "{0} ({1})".format(project_name, platform_name)
    else:
        label += platform_name

    return label


def execute_command(args, shell=False, fail_if_nonzero=True):
    eprint(" ".join(args))
    return subprocess.run(args, shell=shell, check=fail_if_nonzero, env=os.environ).returncode


def download_bazel_binary(dest_dir, platform):
    host_platform = PLATFORMS[platform].get("host-platform", platform)
    binary_path = "bazel-bin/src/bazel"
    if platform == "windows":
        binary_path = r"bazel-bin\src\bazel"

    source_step = create_label(host_platform, "Bazel", build_only=True)
    execute_command(
        ["buildkite-agent", "artifact", "download", binary_path, dest_dir, "--step", source_step]
    )
    bazel_binary_path = os.path.join(dest_dir, binary_path)
    st = os.stat(bazel_binary_path)
    os.chmod(bazel_binary_path, st.st_mode | stat.S_IEXEC)
    return bazel_binary_path
