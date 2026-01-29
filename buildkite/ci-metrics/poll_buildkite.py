import os
import logging
import requests
from google.cloud import bigquery
from datetime import datetime, timezone

# --- Configuration ---
ORGS = ["bazel", "bazel-trusted", "bazel-testing"]
ORG_TOKENS = {
    "bazel": os.environ.get('BUILDKITE_API_TOKEN_BAZEL'),
    "bazel-trusted": os.environ.get('BUILDKITE_API_TOKEN_BAZEL_TRUSTED'),
    "bazel-testing": os.environ.get('BUILDKITE_API_TOKEN_BAZEL_TESTING'),
}
PROJECT_ID = "bazel-public"
DATASET_ID = "bazel_ci_metrics"
TABLE_ID = "infra_stats"

# --- BigQuery Client ---
client = bigquery.Client(project=PROJECT_ID)
table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# --- Buildkite Client ---
class BuildkiteClient:

  def __init__(self, org_slug):
    self.org_slug = org_slug
    self.token = ORG_TOKENS.get(org_slug)

    if not self.token:
      raise ValueError(f"No API Token found for org: {org_slug}")

    self.headers = {'Authorization': f'Bearer {self.token}'}
    self.base_url = f"https://api.buildkite.com/v2/organizations/{org_slug}"

  def _fetch_all_pages(self, endpoint, params=None):
    """
    Fetches all pages from a specific endpoint (e.g. 'agents').
    """
    if params is None:
      params = {}
    # Always request the max page size to minimize requests
    params['per_page'] = 100

    all_items = []
    current_url = f"{self.base_url}/{endpoint}"

    while current_url:
      try:
        resp = requests.get(current_url, headers=self.headers, params=params)
        if resp.status_code != 200:
          print(f"Error fetching {current_url}: {resp.status_code} - {resp.text}")
          break

        data = resp.json()
        if isinstance(data, list):
          all_items.extend(data)

        # Check for next page link in header
        link_header = resp.headers.get("Link", "")
        next_url = None
        if 'rel="next"' in link_header:
          links = link_header.split(", ")
          for link in links:
            if 'rel="next"' in link:
              next_url = link.split(";")[0].strip("<>")
              break

        current_url = next_url
        # Params are usually part of the next_url, so clear them to avoid duplicating
        params = None
      except Exception as e:
        print(f"Exception during pagination: {e}")
        break

    return all_items

  def get_agents(self):
    return self._fetch_all_pages("agents")

  def get_scheduled_jobs(self):
    return self._fetch_all_pages("builds", params={'state': 'scheduled'})

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

  try:
    bk_client = BuildkiteClient(org)
  except ValueError as e:
    logging.error(e)
    return None

  # 1. Agents
  agents = bk_client.get_agents()

  total_agents = len(agents)
  busy_agents = 0
  idle_agents = 0
  disconnected_agents = 0

  # Bootstrap calculation variables
  bootstrap_samples = []

  for a in agents:
    if a.get('job') is not None:
      busy_agents += 1
    if a.get('job') is None and a.get('connection_state') == 'connected':
      idle_agents += 1
    if a.get('connection_state') in ['disconnected', 'lost']:
      disconnected_agents += 1

    created_at_str = a.get('created_at')
    created_dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
    boot_ts = 0 #TODO: update after including it in the agent data
    bootstrap_samples.append((created_dt.timestamp() - boot_ts))

  avg_bootstrap_time = sum(bootstrap_samples) / len(bootstrap_samples) if bootstrap_samples else 0.0

  # 2. Get ALL Scheduled Jobs (Queue Depth)
  scheduled_jobs_list = bk_client.get_scheduled_jobs()
  scheduled_jobs = len(scheduled_jobs_list)

  return {
      "timestamp": datetime.utcnow().isoformat(),
      "org": org,
      "scheduled_jobs": scheduled_jobs,
      "total_agents": total_agents,
      "busy_agents": busy_agents,
      "idle_agents": idle_agents,
      "disconnected_agents": disconnected_agents,
      "avg_bootstrap_time_s": avg_bootstrap_time
  }

def push_to_bigquery(rows):
  if not rows:
    logging.info(f"No data found to push to DB")
    return

  errors = client.insert_rows_json(table_ref, rows)
  if errors:
    logging.error(f"Encountered errors while inserting rows: {errors}")
  else:
    logging.info(f"Successfully inserted {len(rows)} metrics for timestamp {rows[0]['timestamp']}")

def main():
  setup_logging()
  logging.info(f"Starting Buildkite Poller")

  try:
    all_metrics = []
    for org in ORGS:
      metrics = get_org_metrics(org)
      if metrics:
        all_metrics.append(metrics)

    if all_metrics:
      push_to_bigquery(all_metrics)

  except Exception as e:
    logging.critical(f"CRITICAL ERROR in Poller: {e}")

if __name__ == "__main__":
  main()