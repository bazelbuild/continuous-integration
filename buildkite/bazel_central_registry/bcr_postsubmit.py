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

This script does two things:
  - Mirror new archives detected since last synced BCR commit.
  - Sync BCR content to bcr.bazel.build.
"""

import base64
import hashlib
import json
import sys
import subprocess
import tempfile
import urllib.request

BCR_BUCKET = "gs://bcr.bazel.build/"
LAST_SYNCED_COMMIT_URL = BCR_BUCKET + "last_synced_commit"
MIRROR_BUCKET = BCR_BUCKET + "test-mirror/"
MIRROR_URL_PREFIX = "https://bcr.bazel.build/test-mirror/"


class BcrPipelineException(Exception):
    """Raised whenever something goes wrong and we should exit with an error."""


def error(msg):
    raise BcrPipelineException("ERROR: {}".format(msg))


def eprint(*args, **kwargs):
    """
    Print to stderr and flush (just in case).
    """
    print(*args, flush=True, file=sys.stderr, **kwargs)


def print_collapsed_group(name):
    eprint("\n\n--- {0}\n\n".format(name))


def print_expanded_group(name):
    eprint("\n\n+++ {0}\n\n".format(name))


def download(url):
    with urllib.request.urlopen(url) as response:
        return response.read()


def fetch_last_synced_commit():
    print_expanded_group(":gcloud: Fetch last synced commit")
    commit = subprocess.check_output(
        ["gsutil", "cat", LAST_SYNCED_COMMIT_URL]
    ).decode("utf-8").strip()
    eprint("Last synced commit is " + commit)
    return commit


def get_current_commit():
    print_expanded_group(":git: Get current commit")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    eprint("Current commit is " + commit)
    return commit


def parse_new_archive_urls(last_synced_commit):
    # Calcuate changed files since last synced commit
    print_expanded_group(":git: Parse new archive urls")
    lines = subprocess.check_output(
        ["git", "diff", last_synced_commit, "--name-only", "--pretty=format:"]
    ).decode("utf-8").splitlines()

    archive_urls = {}
    for line in lines:
        file = line.strip()
        if file.endswith("source.json"):
            with open(file) as f:
                source = json.load(f)
                archive_urls[source["url"]] = source["integrity"]
                eprint("New archive found: {0} => {1}\n".format(source["url"], source["integrity"]))
    return archive_urls


def remove_prefix(line, prefix):
    if line.startswith(prefix):
        return line[len(prefix):]
    return line


def verify_integrity(data, integrity):
    algo, expected_value = integrity.split("-", 1)
    hash_value = ""
    if algo == "sha256":
        hash_value = hashlib.sha256(data)
    elif algo == "sha384":
        hash_value = hashlib.sha384(data)
    elif algo == "sha512":
        hash_value = hashlib.sha512(data)
    else:
        error("Wrong integrity value format: " + integrity)
    return base64.b64encode(hash_value.digest()).decode() == expected_value


def already_mirrored(target_path):
    try:
        subprocess.check_output(["gsutil", "ls", MIRROR_BUCKET + target_path])
        return True
    except subprocess.CalledProcessError:
        return False


def mirror_archive(url, integrity):
    eprint("Trying to mirror {0}, expected integrity {1}".format(url, integrity))
    if url.startswith("https://"):
        target_path = remove_prefix(url, "https://")
    elif url.startswith("http://"):
        target_path = remove_prefix(url, "http://")
    else:
        error("Wrong archive URL: " + url)

    data = download(url)

    if not verify_integrity(data, integrity):
        error("Integrity value of {0} doesn't match the expected value {1}.".format(url, integrity))

    if already_mirrored(target_path):
        data = download(MIRROR_URL_PREFIX + target_path)
        if not verify_integrity(data, integrity):
            error("Archive URL {0} is already mirrored, but integrity value doesn't match the expected value {1}".format(url, integrity))
        eprint("{} already exists and integrity value matches, skipping.".format(MIRROR_URL_PREFIX + target_path))
    else:
        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        tmpfile.write(data)
        tmpfile.close()
        subprocess.check_output(
            ["gsutil", "-h", "Cache-Control: public, max-age=31536000", "cp", tmpfile.name, MIRROR_BUCKET + target_path]
        )
        eprint("Mirror succeeded, archive available at {}".format(MIRROR_URL_PREFIX + target_path))


def sync_bcr_content():
    print_collapsed_group(":gcloud: Sync BCR content")
    subprocess.check_output(
        ["gsutil", "-h", "Cache-Control:no-cache", "cp", "./bazel_registry.json", BCR_BUCKET]
    )
    subprocess.check_output(
        ["gsutil", "-h", "Cache-Control:no-cache", "-m", "rsync", "-d", "-r", "./modules", BCR_BUCKET + "modules"]
    )


def update_last_synced_commit(current_commit):
    print_collapsed_group(":gcloud: Update last synced commit")
    subprocess.check_output(
        "echo %s | gsutil -h 'Cache-Control: no-cache' cp - %s" % (current_commit, LAST_SYNCED_COMMIT_URL),
        shell=True,
    )
    eprint("Last synced commit updated to " + current_commit)


def main():
    last_synced_commit = fetch_last_synced_commit()
    current_commit = get_current_commit()
    if current_commit == last_synced_commit:
        eprint("Current commit is already synced.")
        return 0
    archive_urls = parse_new_archive_urls(last_synced_commit)
    print_collapsed_group(":gcloud: Mirror archives")
    for url, integrity in archive_urls.items():
        mirror_archive(url, integrity)
    sync_bcr_content()
    update_last_synced_commit(current_commit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
