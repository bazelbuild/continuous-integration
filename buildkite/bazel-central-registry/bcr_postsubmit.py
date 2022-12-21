#!/usr/bin/env python3
#
# Copyright 2018 The Bazel Authors. All rights reserved.
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
# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring
# pylint: disable=unspecified-encoding
# pylint: disable=invalid-name
"""The CI script for Bazel Central Registry Postsubmit.

This script does one thing:
  - Sync the bazel_registry.json and modules/ directory in the main branch of the BCR to https://bcr.bazel.build
"""

import subprocess
import sys

BCR_BUCKET = "gs://bcr.bazel.build/"

def print_expanded_group(name):
    print("\n\n+++ {0}\n\n".format(name))

def sync_bcr_content():
    print_expanded_group(":gcloud: Sync BCR content")
    subprocess.check_output(
        ["gsutil", "-h", "Cache-Control:no-cache", "cp", "./bazel_registry.json", BCR_BUCKET]
    )
    subprocess.check_output(
        ["gsutil", "-h", "Cache-Control:no-cache", "-m", "rsync", "-d", "-r", "./modules", BCR_BUCKET + "modules"]
    )

def main():
    sync_bcr_content()
    return 0

if __name__ == "__main__":
    sys.exit(main())
