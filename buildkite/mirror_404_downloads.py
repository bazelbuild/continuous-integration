#!/usr/bin/env python3
#
# Copyright 2025 The Bazel Authors. All rights reserved.
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

import hashlib
import logging
import os
import re
import subprocess
import sys
import tempfile
from collections import namedtuple
from typing import Any, Dict, List, Optional, Set, Union

import requests
from bazelci import BuildkiteClient, BuildkiteException, execute_command

# --- Color Constants for Terminal Output ---
# These work best in terminals that support ANSI escape codes.
class Colors:
    SUCCESS: str = "\033[92m"  # Green
    SKIPPED: str = "\033[93m"  # Yellow
    FAILED: str = "\033[91m"   # Red
    RESET: str = "\033[0m"     # Reset color


# --- Constants ---
GCS_BUCKET: str = "bazel-mirror"
BUILDKITE_ORG: str = "bazel"
BUILDKITE_PIPELINE: str = "bazel-bazel"
URL_RE: re.Pattern[str] = re.compile(  # Matches URLs with optional URL-encoded characters
    r"Download from (https?://mirror\.bazel\.build\S+)\s+failed: class java.io.FileNotFoundException GET returned 404 Not Found"
)

# A structured way to represent the result of a mirroring operation.
MirrorResult = namedtuple("MirrorResult", ["status", "url", "reason"])


def setup_logging(level: int = logging.INFO) -> None:
    """Configures basic logging for the script."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)-8s - %(message)s",
        stream=sys.stdout,
    )


def get_latest_build(client: BuildkiteClient) -> Dict[str, Any]:
    """Returns the latest finished build object for the master branch."""
    builds = client.get_build_info_list(
        params=[("per_page", 1), ("branch", "master"), ("state", "finished")]
    )
    if not builds:
        raise RuntimeError(
            f"No finished builds found for pipeline '{client.pipeline}' on branch 'master'"
        )
    return builds[0]


def parse_urls_from_logs(logs: str) -> Set[str]:
    """Parses failed download URLs from the given logs."""
    found_urls = URL_RE.findall(logs)
    # URL-decode the found URLs to handle characters like %2B
    decoded_urls = {requests.utils.unquote(url) for url in found_urls}
    return decoded_urls


def mirror_url(url: str, bucket: str) -> MirrorResult:
    """
    Mirrors a single URL to the GCS bucket and returns the result.
    """
    logging.info(f"Processing URL: {url}")
    source_url = url
    mirror_prefix = "https://mirror.bazel.build/"
    if source_url.startswith(mirror_prefix):
        source_url = "https://" + source_url[len(mirror_prefix) :]
        logging.debug(f"URL is on mirror; translating to source: {source_url}")

    target_path = source_url.split("://", 1)[1]
    gcs_url = f"gs://{bucket}/{target_path}"

    try:
        execute_command(["gsutil", "-q", "stat", gcs_url])
        return MirrorResult("SKIPPED", gcs_url, "Artifact already exists")
    except subprocess.CalledProcessError:
        logging.debug("Artifact not found in GCS, proceeding with mirror...")
    except Exception as e:
        return MirrorResult("FAILED", gcs_url, f"GCS check failed: {e}")

    temp_filename = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_filename = temp_file.name
            logging.debug(f"Downloading {source_url} to {temp_filename}...")
            response = requests.get(source_url, stream=True, timeout=300)
            response.raise_for_status()

            hasher = hashlib.sha256()
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
                hasher.update(chunk)
            logging.debug(f"Download complete. SHA256: {hasher.hexdigest()}")

        execute_command(["gsutil", "cp", temp_filename, gcs_url])
        execute_command(
            ["gsutil", "setmeta", "-h", "Cache-Control:public, max-age=31536000", gcs_url]
        )
        return MirrorResult("SUCCESS", gcs_url, "")
    except (requests.exceptions.RequestException, subprocess.CalledProcessError) as e:
        return MirrorResult("FAILED", source_url, str(e))
    finally:
        if temp_filename and os.path.exists(temp_filename):
            os.remove(temp_filename)
            logging.debug(f"Cleaned up temporary file: {temp_filename}")


def get_urls_from_buildkite(client: BuildkiteClient) -> Set[str]:
    """Fetches logs from the latest build and parses them for failed URLs."""
    latest_build = get_latest_build(client)
    build_number = latest_build["number"]
    logging.info(f"Found latest build: #{build_number} ({latest_build['web_url']})")

    logging.info(f"Fetching and parsing logs for build #{build_number}...")
    all_urls_to_mirror: Set[str] = set()
    for job in latest_build.get("jobs", []):
        if job.get("raw_log_url"):
            job_id = job.get("id", "N/A")
            try:
                log_content = client.get_build_log(job)
                if not log_content:
                    logging.warning(f"Log content for job {job_id} is empty. Skipping.")
                    continue

                urls_in_job = parse_urls_from_logs(log_content)
                if urls_in_job:
                    job_url = job.get("web_url", f"job_id: {job_id}")
                    logging.info(f"Found {len(urls_in_job)} failed URL(s) in job: {job_url}")
                    all_urls_to_mirror.update(urls_in_job)

            except BuildkiteException as e:
                logging.error(f"Failed to fetch log for job ID {job_id}: {e}")
                # Continue to next job instead of aborting all

    return all_urls_to_mirror


def mirror_artifacts(urls_to_mirror: Set[str], bucket: str) -> None:
    """Mirrors a set of URLs and prints a final summary."""
    if not urls_to_mirror:
        logging.info("No failed download URLs found. Nothing to do.")
        return

    logging.info(
        f"\nFound a total of {len(urls_to_mirror)} unique URLs to mirror."
    )
    results = [mirror_url(url, bucket) for url in sorted(list(urls_to_mirror))]

    successes = [r for r in results if r.status == "SUCCESS"]
    skips = [r for r in results if r.status == "SKIPPED"]
    failures = [r for r in results if r.status == "FAILED"]

    # --- Final Summary ---
    summary_message = (
        f"Mirroring complete. "
        f"Success: {len(successes)}, Skipped: {len(skips)}, Failed: {len(failures)}"
    )
    logging.info("\n" + "=" * len(summary_message))
    logging.info("Mirroring Summary")
    logging.info("=" * len(summary_message))

    for r in successes:
        logging.info(f"{Colors.SUCCESS}SUCCESS: {r.url}{Colors.RESET}")
    for r in skips:
        logging.warning(f"{Colors.SKIPPED}SKIPPED: {r.url} ({r.reason}){Colors.RESET}")
    for r in failures:
        logging.error(f"{Colors.FAILED}FAILED: {r.url} - Reason: {r.reason}{Colors.RESET}")

    if failures:
        logging.critical("Some artifacts failed to mirror. See errors above.")
        sys.exit(1)


def main() -> None:
    """Main execution function."""
    setup_logging()

    try:
        client = BuildkiteClient(org=BUILDKITE_ORG, pipeline=BUILDKITE_PIPELINE)
        if "BUILDKITE_API_TOKEN" in os.environ:
            client._token = os.environ["BUILDKITE_API_TOKEN"]

        urls = get_urls_from_buildkite(client)
        mirror_artifacts(urls, GCS_BUCKET)

    except (RuntimeError, BuildkiteException) as e:
        logging.critical(f"A critical error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
