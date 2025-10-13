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
from typing import Dict, List, Set

import requests
from bazelci import BuildkiteClient, BuildkiteException

# --- Constants ---
GCS_BUCKET = "bazel-mirror"
BUILDKITE_ORG = "bazel"
BUILDKITE_PIPELINE = "bazel-bazel"
URL_RE = re.compile(
    r"Download from (https?://mirror\.bazel\.build\S+)\s+failed: class java.io.FileNotFoundException GET returned 404 Not Found"
)


def setup_logging():
    """Configures basic logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )


def _run_subprocess(command: List[str]):
    """
    Runs a subprocess command and handles potential errors.

    Args:
        command: A list of strings representing the command to run.

    Raises:
        subprocess.CalledProcessError: If the command returns a non-zero exit code.
    """
    logging.info(f"Running command: {' '.join(command)}")
    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed with exit code {e.returncode}")
        logging.error(f"  Command: {' '.join(command)}")
        logging.error(f"  Stdout: {e.stdout.strip()}")
        logging.error(f"  Stderr: {e.stderr.strip()}")
        raise


def get_latest_build(client: BuildkiteClient) -> Dict:
    """
    Returns the latest finished build object for the master branch.

    Args:
        client: The BuildkiteClient object.

    Returns:
        A dictionary representing the Buildkite build object.

    Raises:
        RuntimeError: If no finished builds are found.
    """
    builds = client.get_build_info_list(
        params=[("per_page", 1), ("branch", "master"), ("state", "finished")]
    )
    if not builds:
        raise RuntimeError(
            f"No finished builds found for pipeline '{BUILDKITE_PIPELINE}' on branch 'master'"
        )
    return builds[0]

def get_job_logs(client: BuildkiteClient, build: Dict) -> Dict[str, str]:
    """
    Gets the logs for all jobs in a build.

    Args:
        client: The BuildkiteClient object.
        build: The Buildkite build object.

    Returns:
        A dictionary mapping job IDs to their log content.
    """
    job_logs: Dict[str, str] = {}

    for job in build.get("jobs", []):
        if job.get("raw_log_url"):
            job_id = job.get("id", "N/A")
            try:
                log_content = client.get_build_log(job)
                if log_content:
                    job_logs[job_id] = log_content
                    logging.info(f"Successfully fetched logs for job ID: {job_id}")
                else:
                    logging.warning(f"Log content for job {job_id} is empty. Skipping.")
            except BuildkiteException as e:
                logging.error(f"Failed to fetch log for job ID {job_id}: {e}. Aborting.")
                raise e
    return job_logs

def parse_urls_from_logs(logs: str) -> Set[str]:
    """Parses failed download URLs from the given logs."""
    return set(URL_RE.findall(logs))

def mirror_url(url: str):
    """
    Mirrors a single URL to the GCS bucket.

    This function downloads the file from the given URL, calculates its SHA256
    hash, uploads it to GCS, and sets public cache headers. It skips
    the upload if the file already exists in the bucket.

    Args:
        url: The URL of the file to mirror.
    """
    logging.info(f"Processing URL: {url}")
    source_url = url
    mirror_prefix = "https://mirror.bazel.build/"
    if source_url.startswith(mirror_prefix):
        source_url = "https://" + source_url[len(mirror_prefix) :]
        logging.info(f"URL is on mirror; translating to source: {source_url}")

    target_path = source_url.split("://", 1)[1]
    gcs_url = f"gs://{GCS_BUCKET}/{target_path}"

    # Check if the file already exists in GCS to avoid re-uploading.
    try:
        # Use `gsutil -q stat` which returns a non-zero exit code if the object doesn't exist.
        subprocess.run(["gsutil", "-q", "stat", gcs_url], check=True, capture_output=True)
        logging.info(f"URL already mirrored, skipping: {gcs_url}")
        return
    except subprocess.CalledProcessError:
        # File doesn't exist, so we proceed to mirror it.
        logging.info(f"URL not found in GCS, proceeding with mirror: {gcs_url}")
        pass
    except Exception as e:
        logging.error(f"An unexpected error occurred while checking GCS for {gcs_url}: {e}")
        return

    temp_filename = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_filename = temp_file.name
            logging.info(f"Downloading {source_url} to {temp_filename}...")
            response = requests.get(source_url, stream=True)
            response.raise_for_status()

            hasher = hashlib.sha256()
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
                hasher.update(chunk)
            digest = hasher.hexdigest()
            logging.info(f"Download complete. SHA256: {digest}")

        _run_subprocess(["gsutil", "cp", temp_filename, gcs_url])
        logging.info(f"Successfully uploaded to {gcs_url}")

        _run_subprocess(
            ["gsutil", "setmeta", "-h", "Cache-Control:public, max-age=31536000", gcs_url]
        )
        logging.info(f"Successfully set metadata on {gcs_url}")
        logging.info(f"Successfully mirrored {source_url}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download {source_url}: {e}")
    except subprocess.CalledProcessError:
        # The _run_subprocess helper already logged the detailed error.
        logging.error(f"Failed to mirror {source_url} due to a gsutil error.")
    finally:
        if temp_filename and os.path.exists(temp_filename):
            os.remove(temp_filename)
            logging.info(f"Cleaned up temporary file: {temp_filename}")

def main():
    """Main execution function."""
    setup_logging()

    try:
        client = BuildkiteClient(org=BUILDKITE_ORG, pipeline=BUILDKITE_PIPELINE)

        # Override client._token from env var BUILDKITE_API_TOKEN if set
        if os.environ.get("BUILDKITE_API_TOKEN"):
            client._token = os.environ.get("BUILDKITE_API_TOKEN")

        logging.info(
            f"Fetching latest build for pipeline '{BUILDKITE_ORG}/{BUILDKITE_PIPELINE}'..."
        )
        latest_build = get_latest_build(client)
        build_number = latest_build["number"]
        build_url = latest_build["web_url"]
        logging.info(f"Found latest build: #{build_number} ({build_url})")

        logging.info(f"Fetching logs for build #{build_number}...")
        logs_by_job = get_job_logs(client, latest_build)
        logging.info("Finished fetching all job logs.")

        logging.info("Parsing logs for failed download URLs...")
        all_urls_to_mirror: Set[str] = set()
        for job_id, logs in logs_by_job.items():
            logging.info(f"--- Parsing logs for job ID: {job_id} ---")
            urls_in_job = parse_urls_from_logs(logs)
            if urls_in_job:
                logging.info(f"Found {len(urls_in_job)} URLs in job {job_id}:")
                for url in sorted(list(urls_in_job)):
                    logging.info(f"  - {url}")
                all_urls_to_mirror.update(urls_in_job)
            else:
                logging.info(f"No failed download URLs found in job {job_id}.")

        if not all_urls_to_mirror:
            logging.info("No failed download URLs found across any jobs. Nothing to do.")
            return

        logging.info(
            f"\nFound a total of {len(all_urls_to_mirror)} unique URLs to mirror across all jobs."
        )
        for url in sorted(list(all_urls_to_mirror)):
            mirror_url(url)
        logging.info("All URLs processed.")

    except (
        RuntimeError,
        requests.exceptions.RequestException,
        subprocess.CalledProcessError,
        BuildkiteException,
    ) as e:
        logging.critical(f"A critical error occurred, aborting script: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()