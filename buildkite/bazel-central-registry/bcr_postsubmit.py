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

import base64
import hashlib
import json
import os
import requests
import subprocess
import sys
import tempfile

BCR_BUCKET = "gs://bcr.bazel.build/"
ATTESTATION_METADATA_FILE = "attestations.json"
FILES_WITH_ATTESTATIONS = ("source.json", "MODULE.bazel")

# Basename of the file that contains the most recent commit
# that passed through the post-submit pipeline successfully.
LAST_GREEN_FILE = "last_green.txt"


class AttestationError(Exception):
    """Raised when there is a problem wrt attestations."""

def print_expanded_group(name):
    print("\n\n+++ {0}\n\n".format(name))

def get_output(command):
    return subprocess.run(
          command,
          encoding='utf-8',
          stdout=subprocess.PIPE,
      ).stdout

def check_and_write_new_attestations():
    print_expanded_group(":cop::copybara: Check & write attestations")
    paths = get_new_attestations_json_paths()
    if not paths:
        # TODO: turn this into an error
        print(f"No {ATTESTATION_METADATA_FILE} files were changed.")
        return

    for p in paths:
        check_and_write_module_attestations(p)


def get_new_attestations_json_paths():
    cwd = os.getcwd()
    cmd = ["git", "diff-tree", "--no-commit-id", "--name-only", "-r"]

    # last_green should be the parent commit. However, sometimes the
    # pipeline can fail due to infra issues. In this case we need
    # to mirror attestations in the commits of the failing runs, too.
    last_green = get_last_green()
    if last_green:
        cmd.append(last_green)

    paths = get_output(cmd + [get_commit()])
    return [os.path.join(cwd, p) for p in paths.split("\n") if p.endswith(f"/{ATTESTATION_METADATA_FILE}")]


def get_last_green():
    url = os.path.join(
        BCR_BUCKET.replace("gs://", "https://storage.googleapis.com/"), LAST_GREEN_FILE
    )
    with requests.get(url) as response:
        if response.status_code != 200:
            return ""

        return response.content.decode("utf-8")


def get_commit():
    return os.getenv("BUILDKITE_COMMIT")


def check_and_write_module_attestations(attestations_json_path):
    print(f"Checking {attestations_json_path}...")
    dest_dir = os.path.dirname(attestations_json_path)
    with open(attestations_json_path, "rb") as af:
        metadata = json.loads(af.read())
    
    for f in FILES_WITH_ATTESTATIONS:
        try:
            entry = metadata["attestations"][f]
            check_and_write_single_attestation(entry["url"], entry["integrity"], dest_dir)
        except Exception as ex:
            raise AttestationError(f"{attestations_json_path} - {f}: {ex}") from ex

    print("Done!")

def check_and_write_single_attestation(url, integrity, dest_dir):
    print(f"\tFound attestation @ {url}")
    with requests.get(url) as response:
        if response.status_code != 200:
            raise AttestationError(f"{url}: HTTP {response.status_code}")

        raw_content = response.content

    check_integrity(raw_content, integrity)
    print("\t\tIntegrity: OK")

    dest = os.path.join(dest_dir, get_canonical_basename(url))
    print(f"\t\tWriting attestation to {dest}...")
    with open(dest, "wb") as f:
        f.write(raw_content)

def check_integrity(data, expected):
    algorithm, _, _ = expected.partition("-")
    assert algorithm in {"sha224", "sha256", "sha384", "sha512"}, "Unsupported SRI algorithm"

    hash = getattr(hashlib, algorithm)(data)
    encoded = base64.b64encode(hash.digest()).decode()
    actual = f"{algorithm}-{encoded}"
    if actual != expected:
        raise AttestationError(f"Expected checksum {expected}, got {actual}.")

# Attestation files in GitHub releases may have prefixes in their basename
# to avoid conflicts when multiple modules are released together
# (e.g. rules_python and rules_python_gazelle_plugin).
# In this case we need to get the canonical basename.
def get_canonical_basename(url):
    actual_basename = os.path.basename(url)
    for f in FILES_WITH_ATTESTATIONS:
        if f in actual_basename:
            return f"{f}.intoto.jsonl"
    
    raise AttestationError(f"Invalid basename of {url}.")


def sync_bcr_content():
    print_expanded_group(":gcloud: Sync BCR content")
    subprocess.check_output(
        ["gsutil", "-h", "Cache-Control:no-cache", "rsync", "-c", "./bazel_registry.json", BCR_BUCKET]
    )
    subprocess.check_output(
        # -c Use checksum to compare files
        # -d Delete files in destination that aren't in source
        ["gsutil", "-h", "Cache-Control:no-cache", "-m", "rsync", "-c", "-d", "-r", "./modules", BCR_BUCKET + "modules"]
    )


def update_last_green():
    path = os.path.join(tempfile.mkdtemp(), LAST_GREEN_FILE)
    with open(path, "wt") as f:
        f.write(get_commit())

    dest = os.path.join(BCR_BUCKET, LAST_GREEN_FILE)
    subprocess.check_output(["gsutil", "cp", path, dest])


def main():
    check_and_write_new_attestations()
    sync_bcr_content()
    update_last_green()
    return 0

if __name__ == "__main__":
    sys.exit(main())
