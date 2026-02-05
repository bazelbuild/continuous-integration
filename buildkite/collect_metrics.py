import os
import json
import base64
import re
import subprocess
import urllib
from datetime import datetime
from collections import defaultdict

# --- Helpers ---

def fetch_job_timestamps(org_slug, pipeline_slug, build_number):
  """
  Fetches real timestamps from Buildkite API for the current job.
  Returns (created_at, started_at, finished_at) strings.
  """
  try:
    from bazelci import BuildkiteClient
    client = BuildkiteClient(org_slug)
    build_data = client.get_build(pipeline_slug, build_number)
    return build_data.get("created_at"), build_data.get(
        "started_at"), build_data.get("finished_at")

  except Exception as e:
    print(f"Warning: Failed to fetch API timestamps: {e}")

  return None, None, None


def get_git_stats(target_dir="."):
  """Gets the number of files changed between HEAD and HEAD~1."""
  try:
    # Runs git diff in the target directory
    output = subprocess.check_output(
        ["git", "diff", "--shortstat", "HEAD~1", "HEAD"],
        cwd=target_dir,
        text=True,
        stderr=subprocess.STDOUT
    ).strip()

    # Output format: " 1 file changed, 1 insertion(+)"
    if "changed" in output:
      # Standard split() handles multiple spaces and leading whitespace automatically
      return int(output.split()[0])

  except Exception as e:
    print(
        f"Warning: Git diff failed ({e}). Defaulting changed_files to large value (9999).")
    # This will be passed by the cahge hit metric, as it only considers small changes.
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
        if not content_b64: continue
        content_str = base64.b64decode(content_b64).decode("utf-8")
        match = re.search(r"Critical Path: ([\d\.]+)s", content_str)
        if match:
          return float(match.group(1))
      except Exception as e:
        print(f"Error parsing critical path log: {e}")
  return 0.0


def parse_bep(filepath):
  """Stream parses the BEP JSON Lines file."""
  metrics = {
      "wall_time_ms": 0,
      "critical_path_s": 0.0,
      "remote_cache_hits": 0,
      "total_actions": 0,
      "output_size_bytes": 0,
      "bytes_downloaded": 0,
      "failed_test_count": 0,
      "exit_code": 0
  }

  target_map = defaultdict(list)
  target_status = {}

  try:
    with open(filepath, 'r') as f:
      for line in f:
        if not line.strip(): continue
        try:
          event = json.loads(line)
        except json.JSONDecodeError:
          print(f"Skipping invalid JSON line")
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
            # If multiple shards, we take the worst status (e.g. if one shard fails, test fails)
            current_status = data.get("status", "UNKNOWN")
            if label not in target_status or current_status != "PASSED":
              target_status[label] = current_status

            # Check for failure to increment counter
            if current_status != "PASSED":
              metrics["failed_test_count"] += 1

        # --- 2. Build Metrics ---
        if "buildMetrics" in event:
          buildMetrics = event["buildMetrics"]
          metrics["wall_time_ms"] = int(
              buildMetrics.get("timingMetrics", {}).get("wallTimeInMs", 0))

          action_summary = buildMetrics.get("actionSummary", {})
          metrics["total_actions"] = int(
              action_summary.get("actionsExecuted", 0))

          # Sum up cache hits from runnerCount
          # We count both remote & disk hists because in both cases, Bazel successfully avoided doing the work again.
          for runner in action_summary.get("runnerCount", []):
            name = runner.get("name", "").lower()
            if "remote cache hit" in name or "disk cache hit" in name:
              metrics["remote_cache_hits"] += int(runner.get("count", 0))

          # Artifacts: Try topLevelArtifacts first, fall back to outputArtifactsSeen
          artifacts = buildMetrics.get("artifactMetrics", {})
          metrics["output_size_bytes"] = int(
              artifacts.get("topLevelArtifacts", {}).get("sizeInBytes", 0))
          if metrics["output_size_bytes"] == 0:
            metrics["output_size_bytes"] = int(
                artifacts.get("outputArtifactsSeen", {}).get("sizeInBytes", 0))

          # Network
          net = buildMetrics.get("networkMetrics", {}).get("systemNetworkStats",
                                                           {})
          metrics["bytes_downloaded"] = int(net.get("bytesRecv", 0))

        # --- 3. Build Tool Logs ---
        if "buildToolLogs" in event:
          logs = event["buildToolLogs"].get("log", [])
          metrics["critical_path_s"] = extract_critical_path(logs)

        # --- Build Finished (Exit Code) ---
        if "buildFinished" in event_id:
          exit_data = event.get("finished").get("exitCode", {})
          metrics["exit_code"] = int(exit_data.get("code", 0))

  except FileNotFoundError:
    print(f"Error: BEP file not found at {filepath}")
    return None, None

  # --- 4. Post-Process Nested Targets ---
  formatted_targets = []
  for label, shards in target_map.items():
    formatted_targets.append({
        "label": label,
        "status": target_status.get(label, "UNKNOWN"),
        "duration_s": max(shards) if shards else 0.0,
        "shard_count": len(shards),
        "shard_durations": shards
    })

  return metrics, formatted_targets


# --- Main Publishing Function ---

def publish_to_bigquery(row):
  """
  Pushes a single row to BigQuery using the REST API directly.
  Zero dependencies required.
  """
  PROJECT_ID = "bazel-public"
  DATASET_ID = "bazel_ci_metrics"
  TABLE_ID = "ci_builds"

  try:
    req = urllib.request.Request("http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token")
    req.add_header("Metadata-Flavor", "Google")
    with urllib.request.urlopen(req) as response:
      token = json.loads(response.read().decode())['access_token']
  except Exception:
    print("Unable to get GCP token from metadata server. Pushing to BigQuery will fail.")
    return

  url = f"https://bigquery.googleapis.com/bigquery/v2/projects/{PROJECT_ID}/datasets/{DATASET_ID}/tables/{TABLE_ID}/insertAll"

  payload = {
      "kind": "bigquery#tableDataInsertAllRequest",
      "rows": [{"json": row}]
  }

  try:
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {token}")

    with urllib.request.urlopen(req) as response:
      result = json.loads(response.read().decode())
      if "insertErrors" in result:
        print(f"BQ Insert Errors: {result['insertErrors']}")
      else:
        print("Successfully pushed metrics to BigQuery via REST.")
  except urllib.error.HTTPError as e:
    print(f"BQ REST API Failed: {e.code} - {e.read().decode()}")
  except Exception as e:
    print(f"BQ REST API Error: {e}")

def collect_metrics_and_push_to_bigquery(bep_file_path):
  """
  Reads the BEP file, collects environment variables, and pushes metrics to BigQuery.
  Call this function from bazelci.py after the build finishes.
  """

  # --- Configuration (Read Env Vars inside function) ---
  BUILDKITE_BUILD_ID = os.getenv("BUILDKITE_BUILD_ID")
  try:
    BUILDKITE_BUILD_NUMBER = int(os.getenv("BUILDKITE_BUILD_NUMBER"))
  except (ValueError, TypeError):
    BUILDKITE_BUILD_NUMBER = 0

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

  #Injected via webhooks
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


  print(f"Starting Metrics Publisher for Build #{BUILDKITE_BUILD_NUMBER}...")

  # 1. Parse Data
  bep_metrics, targets = parse_bep(bep_file_path)
  if bep_metrics is None:
    print("Skipping BigQuery push due to BEP parsing failure.")
    return

  # 2. Get Timestamps & calculate Queue time
  build_created, build_started, build_finished = fetch_job_timestamps(ORG,
                                                                      PIPELINE,
                                                                      BUILDKITE_BUILD_NUMBER)
  queue_duration = 0.0
  try:
    created_dt = datetime.fromisoformat(build_created.replace("Z", "+00:00"))
    started_dt = datetime.fromisoformat(build_started.replace("Z", "+00:00"))
    queue_duration = (started_dt - created_dt).total_seconds()
  except Exception as e:
    print(f"Warning: Could not parse timestamps: {e}")

  # 3. Construct BigQuery Row
  row = {
      "build_id": BUILDKITE_BUILD_ID,
      "build_number": BUILDKITE_BUILD_NUMBER,
      "job_id": BUILDKITE_JOB_ID,
      "job_label": BUILDKITE_LABEL,
      "finished_at": build_finished,
      "created_at": build_created,
      "started_at": build_started,
      "pipeline": PIPELINE,
      "platform": PLATFORM,
      "agent_id": AGENT_ID,
      "branch": BRANCH,
      "repo": REPO,
      "commit_sha": COMMIT_SHA,
      "exit_code": bep_metrics["exit_code"],
      "failed_test_count": bep_metrics["failed_test_count"],
      "retry_count": RETRY_COUNT,
      "wall_time_s": bep_metrics["wall_time_ms"] / 1000.0,
      "critical_path_s": bep_metrics["critical_path_s"],
      "queue_duration_s": queue_duration,
      "checkout_duration_s": CHECKOUT_DURATION_S,
      "prep_duration_s": PREP_DURATION_S,
      "remote_cache_hits": bep_metrics["remote_cache_hits"],
      "total_actions": bep_metrics["total_actions"],
      "output_size_bytes": bep_metrics["output_size_bytes"],
      "bytes_downloaded": bep_metrics["bytes_downloaded"],
      "changed_files_count": CHANGED_FILES_COUNT,
      "targets": targets
  }

  # BigQuery Config
  PROJECT_ID = "bazel-public"
  DATASET_ID = "bazel_ci_metrics"
  TABLE_ID = "ci_builds"

  # 4. Push to BigQuery
  #TODO use this for now to avoid extra dependencies
  publish_to_bigquery(row)
  # client = bigquery.Client(project=PROJECT_ID)
  # table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
  #
  # print(f"Pushing row to {table_ref}...")
  # errors = client.insert_rows_json(table_ref, [row])
  #
  # if errors:
  #   print(f"BQ Insert Errors: {errors}")
  #   print(json.dumps(row, indent=2))
  # else:
  #   print("Success: Metrics pushed to BigQuery.")
