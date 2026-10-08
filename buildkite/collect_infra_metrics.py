import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime

from google.cloud import bigquery

from bazelci import BuildkiteClient

# --- Configuration ---
ORGs = ["bazel-testing", "bazel", "bazel-trusted"]
PROJECT_ID = "bazel-untrusted"
DATASET_ID = "bazel_ci_metrics"
TABLE_ID = "infra_stats"


def setup_logging(level=logging.INFO):
  """Configures basic logging for the script."""
  logging.basicConfig(
      level=level,
      format="%(asctime)s - %(levelname)-8s - %(message)s",
      stream=sys.stdout,
  )


def get_expected_agents():
  """Fetches expected agent counts per (org, platform) for GCE and Mac pools."""
  expected = {}
  try:
    for project in ("bazel-untrusted", "bazel-public"):
      out = subprocess.check_output([
          "gcloud", "compute", "instance-groups", "managed", "list",
          f"--project={project}", "--format=json(name,targetSize)",
      ])
      for g in json.loads(out):
        name = g.get("name", "")
        if not name.startswith("bk-"):
          continue
        org = (
            "bazel-testing" if "-testing-" in name
            else "bazel-trusted" if "-trusted-" in name else "bazel"
        )
        platform = (
            "linux_arm64" if name.endswith("-arm64")
            else "windows" if name.endswith("windows") else "linux"
        )
        expected[(org, platform)] = expected.get((org, platform), 0) + int(g.get("targetSize", 0))

    # Mac pools live in MacService config (not GCP), so use the 7-day observed max.
    query = (
        f"SELECT org, platform, MAX(total_agents) AS expected_agents "
        f"FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}` "
        f"WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY) "
        f"AND platform IN ('macos', 'macos_arm64') GROUP BY 1, 2"
    )
    for r in bigquery.Client(project="bazel-public").query(query).result():
      if r["expected_agents"] is not None:
        expected[(r["org"], r["platform"])] = int(r["expected_agents"])
  except Exception as e:
    logging.warning(f"Failed to fetch expected agent sizes: {e}")
  return expected

def extract_platform(tags):
  """Extracts the platform from agent meta_data tags."""
  for tag in tags:
    if tag.startswith("queue="):
      q = tag.split("=", 1)[1].strip()
      return {"default": "linux", "arm64": "linux_arm64"}.get(q, q)
  return "linux"

def calculate_agent_stats(agents):
  """Computes agent stats grouped by platform."""
  agents_by_platform = {
      "linux": {"total": 0, "busy": 0, "idle": 0, "disconnected": 0, "bootstrap_samples": []},
      "linux_arm64": {"total": 0, "busy": 0, "idle": 0, "disconnected": 0, "bootstrap_samples": []},
      "macos": {"total": 0, "busy": 0, "idle": 0, "disconnected": 0, "bootstrap_samples": []},
      "macos_arm64": {"total": 0, "busy": 0, "idle": 0, "disconnected": 0, "bootstrap_samples": []},
      "windows": {"total": 0, "busy": 0, "idle": 0, "disconnected": 0, "bootstrap_samples": []},
  }

  for a in agents:
    platform = extract_platform(a.get("meta_data", []))
    if platform not in agents_by_platform:
      agents_by_platform[platform] = {
          "total": 0, "busy": 0, "idle": 0, "disconnected": 0, "bootstrap_samples": []
      }
    platform_stats = agents_by_platform[platform]
    platform_stats["total"] += 1
    if a.get('job'):
      platform_stats["busy"] += 1
    if not a.get('job') and a.get('connection_state') == 'connected':
      platform_stats["idle"] += 1
    if a.get('connection_state') in ['disconnected', 'lost']:
      platform_stats["disconnected"] += 1

    created_at_str = a.get('created_at')
    if created_at_str:
      created_dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
      boot_ts = 0  # TODO: update after including it in the agent data
      platform_stats["bootstrap_samples"].append((created_dt.timestamp() - boot_ts))

  return agents_by_platform


def count_scheduled_jobs(builds):
  """Counts scheduled jobs grouped by platform."""
  scheduled_by_platform = {"linux": 0, "linux_arm64": 0, "macos": 0, "macos_arm64": 0, "windows": 0}
  for build in builds:
    for job in build.get("jobs", []):
      if job.get("state") == "scheduled":
        platform = extract_platform(job.get("agent_query_rules", []))
        scheduled_by_platform[platform] = scheduled_by_platform.get(platform, 0) + 1
  return scheduled_by_platform


def get_org_metrics(org, expected_by_pool=None):
  """Fetches metrics for a single org and calculates stats per platform."""
  logging.info(f"Pulling Data for Org: {org}")
  bk_client = BuildkiteClient(org=org)

  # 1. Fetch & Calculate Agent Stats
  agents = bk_client.get_agents()
  logging.info(f"Agent data pulled successfully")
  agents_by_platform = calculate_agent_stats(agents)

  # 2. Fetch & Count Scheduled Jobs (Queue Depth)
  builds = bk_client.get_active_builds()
  logging.info(f"Active builds data pulled successfully")
  scheduled_by_platform = count_scheduled_jobs(builds)

  timestamp = datetime.utcnow().isoformat()
  rows = []

  for platform, stats in agents_by_platform.items():
    scheduled_jobs = scheduled_by_platform.get(platform, 0)
    expected_agents = (expected_by_pool or {}).get((org, platform))

    #Skip platforms with no info (didn't run any jobs)
    if stats["total"] == 0 and scheduled_jobs == 0 and (expected_agents or 0) <= 0:
      continue

    avg_bootstrap_time = sum(stats["bootstrap_samples"]) / len(
        stats["bootstrap_samples"]) if stats["bootstrap_samples"] else 0.0

    rows.append({
        "timestamp": timestamp,
        "org": org,
        "platform": platform,
        "scheduled_jobs": scheduled_jobs,
        "total_agents": stats["total"],
        "busy_agents": stats["busy"],
        "idle_agents": stats["idle"],
        "disconnected_agents": stats["disconnected"],
        "avg_bootstrap_time_s": avg_bootstrap_time,
        "expected_agents": expected_agents,
    })

  return rows

def push_to_bigquery(rows, retries):
  if not rows:
    logging.info("No data found to push to DB")
    return

  client = bigquery.Client(project=PROJECT_ID)
  table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

  logging.info(f"Pushing {len(rows)} rows to BigQuery...")

  for attempt in range(retries):
    errors = client.insert_rows_json(table_ref, rows)
    if not errors:
      logging.info(
          f"Successfully inserted {len(rows)} metrics for timestamp {rows[0]['timestamp']}")
      return

    logging.warning(
        f"Attempt {attempt + 1}/{retries} failed with errors: {errors}")
    if attempt < retries - 1:
      time.sleep(2 ** attempt)

  # If all retries failed
  logging.error(f"Failed to insert rows after {retries} attempts.")
  sys.exit(1)

def main():
  setup_logging()
  logging.info(f"Starting Buildkite Poller")

  try:
    expected_by_pool = get_expected_agents()
    all_metrics = []
    for org in ORGs:
      metrics = get_org_metrics(org, expected_by_pool)
      if metrics:
        all_metrics.extend(metrics)

    if all_metrics:
      push_to_bigquery(all_metrics, 5)

  except Exception as e:
    logging.critical(f"ERROR in Poller: {e}")
    sys.exit(1)


if __name__ == "__main__":
  main()
