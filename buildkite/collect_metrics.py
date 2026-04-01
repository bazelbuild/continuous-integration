import os
import json
import base64
import re
import subprocess
import urllib
import urllib.request
import tempfile

from datetime import datetime
from collections import defaultdict

from bazelci import execute_command, BuildkiteClient, is_windows

from dataclasses import dataclass, field, asdict
from typing import List

@dataclass
class JobTimestamps:
    created_at: str = None
    started_at: str = None
    finished_at: str = None

@dataclass
class TestTarget:
    label: str
    status: str
    duration_s: float
    shard_count: int = 1
    shard_durations: List[float] = field(default_factory=list)

# --- BigQuery Configuration constants ---
PROJECT_ID = "bazel-public"
DATASET_ID = "bazel_ci_metrics"
TABLE_ID = "ci_builds"

@dataclass
class BuildMetrics:
    wall_time_ms: int = 0
    critical_path_s: float = 0.0
    remote_and_disk_cache_hits: int = 0
    total_actions: int = 0
    output_size_bytes: int = 0
    bytes_downloaded: int = 0
    failed_test_count: int = 0
    exit_code: int = 0
    targets: List[TestTarget] = field(default_factory=list)

def print_and_annotate_warning(message):
    """
    Prints a warning to the logs and annotates the Buildkite UI so it's visible on the build page.
    """
    print(message)
    try:
        job_url = f"{os.getenv('BUILDKITE_BUILD_URL')}#{os.getenv('BUILDKITE_JOB_ID')}"
        execute_command(
            [
                "buildkite-agent",
                "annotate",
                "--style=warning",
                f"{message} (for [this job]({job_url}))",
                "--context",
                "ctx-metrics_upload_failed",
            ],
            fail_if_nonzero=False,
        )
    except Exception as e:
        print(f"Failed to annotate Buildkite: {e}")


def fetch_job_timestamps(org_slug, pipeline_slug, build_number, job_id):
    """
    Fetches real timestamps from Buildkite API for the current job.
    Returns:
        JobTimestamps: An object containing created_at, started_at, and finished_at strings.
    """
    try:
        client = BuildkiteClient(org_slug, pipeline_slug)
        build_data = client.get_build_info(build_number)
        for job in build_data.get("jobs", []):
            if job.get("id") == job_id:
                # If the job is still running when this script executes, finished_at is None
                finished_at = job.get("finished_at")
                if not finished_at:
                    # Format as UTC ISO string to match Buildkite's format (e.g. 2023-10-25T10:00:00.000Z)
                    finished_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                return JobTimestamps(
                    created_at=job.get("created_at"),
                    started_at=job.get("started_at"),
                    finished_at=finished_at,
                )
    except Exception as e:
        print(f"Warning: Failed to fetch job timestamps: {e}")

    return JobTimestamps()


def get_git_stats(target_dir="."):
    """Gets the number of files changed between HEAD and HEAD~1."""
    try:
        # Use git show instead of diff HEAD~1 because PRs might be squashed or shallow cloned
        # --shortstat gives a summary of "X files changed" includes NEW and DELETED files too
        output = subprocess.check_output(
            ["git", "show", "--shortstat", "--format="],
            cwd=target_dir,
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
        # Output format: " 1 file changed, 1 insertion(+)"
        match = re.search(r"(\d+)\s+file[s]?\s+changed", output)
        if match:
            return int(match.group(1))
    except Exception as e:
        print(f"Warning: Git diff failed ({e}). Defaulting changed_files to large value (9999).")
    
    # This will be passed by the cache hit metric, as it only considers small changes.
    # but we can also return -1 and update Grafana to skip these values.
    return 9999


def extract_critical_path(build_tool_logs):
    """
    Decodes the 'critical path' log from Base64 and extracts the duration.
    """
    for log in build_tool_logs:
        if log.get("name") == "critical path":
            try:
                content_b64 = log.get("contents")
                if not content_b64:
                    continue
                content_str = base64.b64decode(content_b64).decode("utf-8")
                match = re.search(r"Critical Path: ([\d\.]+)s", content_str)
                if match:
                    return float(match.group(1))
            except Exception as e:
                print(f"Error parsing critical path log: {e}")
    return 0.0


def parse_bep(filepath):
    """
    Parses the Build Event Protocol (BEP) JSON file to extract build metrics and targets.

    Returns:
        BuildMetrics: An object containing aggregated build metrics and test targets.
        None: If the file does not exist.
    """

    if not os.path.exists(filepath):
        print(f"Error: BEP file not found at {filepath}")
        return None

    build_metrics = BuildMetrics()
    target_map = defaultdict(list)
    target_status = {}

    with open(filepath, "r") as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON line at line {line_num}")
                continue

            event_id = event.get("id", {})

            # --- 1. Test Results ---
            if "testResult" in event:
                data = event["testResult"]
                label = event_id.get("testResult", {}).get("label")

                if label:
                    duration_ms = int(data.get("testAttemptDurationMillis", 0))
                    duration_s = duration_ms / 1000.0
                    target_map[label].append(duration_s)

                    # Status (PASSED, FAILED, FLAKY)
                    current_status = data.get("status", "UNKNOWN")
                    if label not in target_status or current_status != "PASSED":
                        target_status[label] = current_status

                    if current_status != "PASSED":
                        build_metrics.failed_test_count += 1

            # --- 2. Build Metrics ---
            elif "buildMetrics" in event:
                buildMetrics = event["buildMetrics"]
                build_metrics.wall_time_ms = int(
                    buildMetrics.get("timingMetrics", {}).get("wallTimeInMs", 0)
                )

                action_summary = buildMetrics.get("actionSummary", {})
                build_metrics.total_actions = int(action_summary.get("actionsExecuted", 0))

                for runner in action_summary.get("runnerCount", []):
                    name = runner.get("name", "").lower()
                    if "remote cache hit" in name or "disk cache hit" in name:
                        build_metrics.remote_and_disk_cache_hits += int(runner.get("count", 0))

                artifacts = buildMetrics.get("artifactMetrics", {})
                build_metrics.output_size_bytes = int(
                    artifacts.get("topLevelArtifacts", {}).get("sizeInBytes", 0)
                )
                if build_metrics.output_size_bytes == 0:
                    build_metrics.output_size_bytes = int(
                        artifacts.get("outputArtifactsSeen", {}).get("sizeInBytes", 0)
                    )

                # Network
                net = buildMetrics.get("networkMetrics", {}).get("systemNetworkStats", {})
                build_metrics.bytes_downloaded = int(net.get("bytesRecv", 0))

            # --- 3. Build Tool Logs ---
            elif "buildToolLogs" in event:
                logs = event["buildToolLogs"].get("log", [])
                build_metrics.critical_path_s = extract_critical_path(logs)

            # --- Build Finished (Exit Code) ---
            if "buildFinished" in event_id:
                exit_data = event.get("finished").get("exitCode", {})
                build_metrics.exit_code = int(exit_data.get("code", 0))

    # --- 4. Post-Process Nested Targets ---
    for label, shards in target_map.items():
        build_metrics.targets.append(
            TestTarget(
                label=label,
                status=target_status.get(label, "UNKNOWN"),
                duration_s=max(shards) if shards else 0.0,
                shard_count=len(shards),
                shard_durations=shards,
            )
        )

    return build_metrics


def publish_to_bigquery(row):
    """
    Pushes a single row to BigQuery using the 'bq' CLI tool via subprocess.
    """

    print(f"Publishing Metrics to BigQuery ...")
    table_ref = f"{PROJECT_ID}:{DATASET_ID}.{TABLE_ID}"        
    bq_cmd = "bq.cmd" if is_windows() else "bq"

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
            json.dump(row, tf)
            tf.write("\n")
            temp_path = tf.name

        result = subprocess.run(
            [bq_cmd, "insert", table_ref, temp_path],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print_and_annotate_warning(f"BigQuery CLI Insert Error:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
            return
            
        print("Success: Metrics pushed to BigQuery via CLI.")
            
    except Exception as e:
        print_and_annotate_warning(f"Failed to execute bq CLI: {e}")
    finally:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)

def collect_metrics_and_push_to_bigquery(bep_file_path):

    print(f"Collecting CI Metrics ...")

    """
    Reads the BEP file, collects environment variables, and pushes metrics to BigQuery.
    Called from bazelci.py after the build finishes.
    """

    # --- Configuration (Read Env Vars inside function) ---
    BUILDKITE_BUILD_ID = os.getenv("BUILDKITE_BUILD_ID")
    BUILDKITE_BUILD_NUMBER = int(os.getenv("BUILDKITE_BUILD_NUMBER"))
    BUILDKITE_JOB_ID = os.getenv("BUILDKITE_JOB_ID")
    BUILDKITE_LABEL = os.getenv("BUILDKITE_LABEL")
    PIPELINE = os.getenv("BUILDKITE_PIPELINE_SLUG")
    ORG = os.getenv("BUILDKITE_ORGANIZATION_SLUG")
    REPO = os.getenv("BUILDKITE_REPO")
    PLATFORM = os.getenv("BUILDKITE_AGENT_META_DATA_OS")
    AGENT_ID = os.getenv("BUILDKITE_AGENT_ID")
    BRANCH = os.getenv("BUILDKITE_BRANCH", "main")
    COMMIT_SHA = os.getenv("BUILDKITE_COMMIT")
    RETRY_COUNT = int(os.getenv("BUILDKITE_RETRY_COUNT", "0"))

    # Injected via webhooks
    try:
        CHECKOUT_DURATION_S = float(os.getenv("CHECKOUT_DURATION_S", "0.0"))
    except ValueError:
        CHECKOUT_DURATION_S = 0.0
    try:
        PREP_DURATION_S = float(os.getenv("PREP_DURATION_S", "0.0"))
    except ValueError:
        PREP_DURATION_S = 0.0

    # Calculate Changed Files
    CHANGED_FILES_COUNT = get_git_stats()

    # Parse BEP Data
    build_metrics = parse_bep(bep_file_path)
    if build_metrics is None:
        print_and_annotate_warning("Skipping BigQuery push due to BEP parsing failure.")
        return

    # Get Timestamps & calculate Queue time
    timestamps = fetch_job_timestamps(
        ORG, PIPELINE, BUILDKITE_BUILD_NUMBER, BUILDKITE_JOB_ID
    )
    queue_duration = 0.0
    if timestamps.created_at and timestamps.started_at:
        try:
            created_dt = datetime.fromisoformat(timestamps.created_at.replace("Z", "+00:00"))
            started_dt = datetime.fromisoformat(timestamps.started_at.replace("Z", "+00:00"))
            queue_duration = (started_dt - created_dt).total_seconds()
        except Exception as e:
            print(f"Warning: Could not parse timestamps: {e}")

    # Construct BigQuery Row
    row = {
        "build_id": BUILDKITE_BUILD_ID,
        "build_number": BUILDKITE_BUILD_NUMBER,
        "job_id": BUILDKITE_JOB_ID,
        "job_label": BUILDKITE_LABEL,
        "finished_at": timestamps.finished_at,
        "created_at": timestamps.created_at,
        "started_at": timestamps.started_at,
        "pipeline": PIPELINE,
        "platform": PLATFORM,
        "agent_id": AGENT_ID,
        "branch": BRANCH,
        "repo": REPO,
        "commit_sha": COMMIT_SHA,
        "exit_code": build_metrics.exit_code,
        "failed_test_count": build_metrics.failed_test_count,
        "retry_count": RETRY_COUNT,
        "wall_time_s": build_metrics.wall_time_ms / 1000.0,
        "critical_path_s": build_metrics.critical_path_s,
        "queue_duration_s": queue_duration,
        "checkout_duration_s": CHECKOUT_DURATION_S,
        "prep_duration_s": PREP_DURATION_S,
        "remote_and_disk_cache_hits": build_metrics.remote_and_disk_cache_hits,
        "total_actions": build_metrics.total_actions,
        "output_size_bytes": build_metrics.output_size_bytes,
        "bytes_downloaded": build_metrics.bytes_downloaded,
        "changed_files_count": CHANGED_FILES_COUNT,
        "targets": [asdict(t) for t in build_metrics.targets],
    }

    publish_to_bigquery(row)
