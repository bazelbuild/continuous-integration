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

import datetime
import tempfile
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess

from config import PLATFORMS
from utils import (
    eprint,
    gsutil_command,
    download_bazel_binary,
    execute_command,
    bazelci_builds_gs_url,
)


class BinaryUploadRaceException(Exception):
    """
    Raised when try_publish_binaries wasn't able to publish a set of binaries,
    because the generation of the current file didn't match the expected value.
    """


def bazelci_builds_metadata_url():
    return "gs://bazel-builds/metadata/latest.json"


def latest_generation_and_build_number():
    output = None
    attempt = 0
    while attempt < 5:
        output = subprocess.check_output(
            [gsutil_command(), "stat", bazelci_builds_metadata_url()], env=os.environ
        )
        match = re.search("Generation:[ ]*([0-9]+)", output.decode("utf-8"))
        if not match:
            raise Exception("Couldn't parse generation. gsutil output format changed?")
        generation = match.group(1)

        match = re.search(r"Hash \(md5\):[ ]*([^\s]+)", output.decode("utf-8"))
        if not match:
            raise Exception("Couldn't parse md5 hash. gsutil output format changed?")
        expected_md5hash = base64.b64decode(match.group(1))

        output = subprocess.check_output(
            [gsutil_command(), "cat", bazelci_builds_metadata_url()], env=os.environ
        )
        hasher = hashlib.md5()
        hasher.update(output)
        actual_md5hash = hasher.digest()

        if expected_md5hash == actual_md5hash:
            break
        attempt += 1
    info = json.loads(output.decode("utf-8"))
    return (generation, info["build_number"])


def sha256_hexdigest(filename):
    sha256 = hashlib.sha256()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
    return sha256.hexdigest()


def bazelci_builds_download_url(platform, git_commit):
    return "https://storage.googleapis.com/bazel-builds/artifacts/{0}/{1}/bazel".format(
        platform, git_commit
    )


def try_publish_binaries(build_number, expected_generation):
    now = datetime.datetime.now()
    git_commit = os.environ["BUILDKITE_COMMIT"]
    info = {
        "build_number": build_number,
        "build_time": now.strftime("%d-%m-%Y %H:%M"),
        "git_commit": git_commit,
        "platforms": {},
    }
    for platform in (name for name in PLATFORMS if PLATFORMS[name]["publish_binary"]):
        tmpdir = tempfile.mkdtemp()
        try:
            bazel_binary_path = download_bazel_binary(tmpdir, platform)
            execute_command(
                [
                    gsutil_command(),
                    "cp",
                    "-a",
                    "public-read",
                    bazel_binary_path,
                    bazelci_builds_gs_url(platform, git_commit),
                ]
            )
            info["platforms"][platform] = {
                "url": bazelci_builds_download_url(platform, git_commit),
                "sha256": sha256_hexdigest(bazel_binary_path),
            }
        finally:
            shutil.rmtree(tmpdir)
    tmpdir = tempfile.mkdtemp()
    try:
        info_file = os.path.join(tmpdir, "info.json")
        with open(info_file, mode="w", encoding="utf-8") as fp:
            json.dump(info, fp, indent=2, sort_keys=True)

        try:
            execute_command(
                [
                    gsutil_command(),
                    "-h",
                    "x-goog-if-generation-match:" + expected_generation,
                    "-h",
                    "Content-Type:application/json",
                    "cp",
                    "-a",
                    "public-read",
                    info_file,
                    bazelci_builds_metadata_url(),
                ]
            )
        except subprocess.CalledProcessError:
            raise BinaryUploadRaceException()
    finally:
        shutil.rmtree(tmpdir)


def main():
    """
    Publish Bazel binaries to GCS.
    """
    current_build_number = os.environ.get("BUILDKITE_BUILD_NUMBER", None)
    if not current_build_number:
        raise Exception("Not running inside Buildkite")
    current_build_number = int(current_build_number)

    for _ in range(5):
        latest_generation, latest_build_number = latest_generation_and_build_number()

        if current_build_number <= latest_build_number:
            eprint(
                (
                    "Current build '{0}' is not newer than latest published '{1}'. "
                    + "Skipping publishing of binaries."
                ).format(current_build_number, latest_build_number)
            )
            break

        try:
            try_publish_binaries(current_build_number, latest_generation)
        except BinaryUploadRaceException:
            # Retry.
            continue

        eprint(
            "Successfully updated '{0}' to binaries from build {1}.".format(
                bazelci_builds_metadata_url(), current_build_number
            )
        )
        break
    else:
        raise Exception("Could not publish binaries, ran out of attempts.")
