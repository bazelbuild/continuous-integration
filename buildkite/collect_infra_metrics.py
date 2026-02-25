import logging
import os
import sys
import time
from datetime import datetime

from google.cloud import bigquery

from bazelci import BuildkiteClient, decrypt_token

# --- Configuration ---
ORGs = ["bazel-trusted", "bazel-testing", "bazel"]
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


def get_org_metrics(org):
  """Fetches metrics for a single org and calculates stats."""
  logging.info(f"Pulling Data for Org: {org}")
  bk_client = BuildkiteClient(org=org)
  bk_client._token = _get_buildkite_token(org)

  # 1. Agents
  agents = bk_client.get_agents()
  logging.info(f"Agent data pulled sucessfully for {len(agents)} agents")

  busy_agents = 0
  idle_agents = 0
  disconnected_agents = 0
  bootstrap_samples = []

  for a in agents:
    if a.get('job'):
      busy_agents += 1
    if not a.get('job') and a.get('connection_state') == 'connected':
      idle_agents += 1
    if a.get('connection_state') in ['disconnected', 'lost']:
      disconnected_agents += 1

    created_at_str = a.get('created_at')
    created_dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
    boot_ts = 0  # TODO: update after including it in the agent data
    bootstrap_samples.append((created_dt.timestamp() - boot_ts))

  avg_bootstrap_time = sum(bootstrap_samples) / len(
      bootstrap_samples) if bootstrap_samples else 0.0

  # 2. Get ALL Scheduled Jobs (Queue Depth)
  scheduled_jobs_list = bk_client.get_scheduled_jobs()
  logging.info(f"Scheduled Jobs pulled sucessfully")

  return {
      "timestamp": datetime.utcnow().isoformat(),
      "org": org,
      "scheduled_jobs": len(scheduled_jobs_list),
      "total_agents": len(agents),
      "busy_agents": busy_agents,
      "idle_agents": idle_agents,
      "disconnected_agents": disconnected_agents,
      "avg_bootstrap_time_s": avg_bootstrap_time
  }

def _get_buildkite_token(org):
  return decrypt_token(
    encrypted_token=(
      BuildkiteClient._ENCRYPTED_BUILDKITE_TRUSTED_API_TOKEN
      if org == "bazel-trusted"
      else BuildkiteClient._ENCRYPTED_BUILDKITE_TESTING_API_TOKEN
      if org == "bazel-testing"
      else BuildkiteClient._ENCRYPTED_BUILDKITE_UNTRUSTED_API_TOKEN
    ),
    kms_key=(
      "buildkite-trusted-api-token"
      if org == "bazel-trusted"
      else "buildkite-testing-api-token"
      if org == "bazel-testing"
      else "buildkite-untrusted-api-token"
    ),
    project=("bazel-public" if org == "bazel-trusted" else "bazel-untrusted"),
  )

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
        all_metrics.append(metrics)

    if all_metrics:
      push_to_bigquery(all_metrics, 5)

  except Exception as e:
    logging.critical(f"ERROR in Poller: {e}")
    sys.exit(1)


if __name__ == "__main__":
  main()
