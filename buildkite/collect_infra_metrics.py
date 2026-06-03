import logging
import os
import sys
import time
from datetime import datetime

from google.cloud import bigquery

from bazelci import BuildkiteClient

# --- Configuration ---
ORGs = ["bazel-testing", "bazel", "bazel-trusted"]
PROJECT_ID = "bazel-public"
DATASET_ID = "bazel_ci_metrics"
TABLE_ID = "infra_stats"


def setup_logging(level=logging.INFO):
  """Configures basic logging for the script."""
  logging.basicConfig(
      level=level,
      format="%(asctime)s - %(levelname)-8s - %(message)s",
      stream=sys.stdout,
  )

def get_agent_platform(agent):
  """Extracts the platform from agent meta_data tags."""
  tags = {}
  for tag in agent.get("meta_data", []):
    if "=" in tag:
      key, value = tag.split("=", 1)
      tags[key.strip()] = value.strip()
  return tags.get("os") or "linux"


def get_job_platform(job):
  """Maps a job's targeted queue to a platform (linux, macos, windows)."""
  rules = job.get("agent_query_rules", [])
  for rule in rules:
    if rule.startswith("queue="):
      queue = rule.split("=", 1)[1].lower()
      if "windows" in queue:
        return "windows"
      elif "macos" in queue:
        return "macos"
  return "linux"


def calculate_agent_stats(agents):
  """Computes agent stats grouped by platform."""
  agents_by_platform = {
      "linux": {"total": 0, "busy": 0, "idle": 0, "disconnected": 0, "bootstrap_samples": []},
      "macos": {"total": 0, "busy": 0, "idle": 0, "disconnected": 0, "bootstrap_samples": []},
      "windows": {"total": 0, "busy": 0, "idle": 0, "disconnected": 0, "bootstrap_samples": []},
  }

  for a in agents:
    platform = get_agent_platform(a)
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
  scheduled_by_platform = {"linux": 0, "macos": 0, "windows": 0}
  for build in builds:
    for job in build.get("jobs", []):
      if job.get("state") == "scheduled":
        platform = get_job_platform(job)
        scheduled_by_platform[platform] += 1
  return scheduled_by_platform


def get_org_metrics(org):
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
    avg_bootstrap_time = sum(stats["bootstrap_samples"]) / len(
        stats["bootstrap_samples"]) if stats["bootstrap_samples"] else 0.0

    rows.append({
        "timestamp": timestamp,
        "org": org,
        "platform": platform,
        "scheduled_jobs": scheduled_by_platform.get(platform, 0),
        "total_agents": stats["total"],
        "busy_agents": stats["busy"],
        "idle_agents": stats["idle"],
        "disconnected_agents": stats["disconnected"],
        "avg_bootstrap_time_s": avg_bootstrap_time
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
    all_metrics = []
    for org in ORGs:
      metrics = get_org_metrics(org)
      if metrics:
        all_metrics.extend(metrics)

    if all_metrics:
      push_to_bigquery(all_metrics, 5)

  except Exception as e:
    logging.critical(f"ERROR in Poller: {e}")
    sys.exit(1)


if __name__ == "__main__":
  main()
