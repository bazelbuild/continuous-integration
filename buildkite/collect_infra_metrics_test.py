import unittest
from unittest.mock import MagicMock, patch

import collect_infra_metrics


class TestCollectInfraMetrics(unittest.TestCase):

  def test_build_agent_rows_busy_and_idle(self):
    agents = [
        {
            "id": "agent-1",
            "name": "bk-docker-busy1",
            "hostname": "bk-docker-busy1",
            "paused": False,
            "paused_at": None,
            "connected_at": "2026-10-21T06:00:00.000Z",
            "last_job_finished_at": None,
            "meta_data": ["queue=default"],
            "job": {
                "state": "running",
                "started_at": "2026-10-21T06:05:00.000Z",
                "web_url": "https://buildkite.com/bazel/bazel-bazel/builds/1#job-1",
            },
        },
        {
            "id": "agent-2",
            "name": "bk-docker-arm64-idle1",
            "hostname": "bk-docker-arm64-idle1",
            "paused": True,
            "paused_at": "2026-10-21T09:00:00.000Z",
            "connected_at": "2026-10-21T08:00:00.000Z",
            "last_job_finished_at": "2026-10-21T08:30:00.000Z",
            "meta_data": ["queue=arm64"],
            "job": None,
        },
    ]

    rows = collect_infra_metrics.build_agent_rows(agents, "bazel", "2026-10-21T10:00:00")

    self.assertEqual(
        rows,
        [
            {
                "timestamp": "2026-10-21T10:00:00",
                "org": "bazel",
                "platform": "linux",
                "id": "agent-1",
                "name": "bk-docker-busy1",
                "hostname": "bk-docker-busy1",
                "paused": False,
                "paused_at": None,
                "connected_at": "2026-10-21T06:00:00.000Z",
                "last_job_finished_at": None,
                "job_state": "running",
                "job_started_at": "2026-10-21T06:05:00.000Z",
                "job_web_url": "https://buildkite.com/bazel/bazel-bazel/builds/1#job-1",
            },
            {
                "timestamp": "2026-10-21T10:00:00",
                "org": "bazel",
                "platform": "linux_arm64",
                "id": "agent-2",
                "name": "bk-docker-arm64-idle1",
                "hostname": "bk-docker-arm64-idle1",
                "paused": True,
                "paused_at": "2026-10-21T09:00:00.000Z",
                "connected_at": "2026-10-21T08:00:00.000Z",
                "last_job_finished_at": "2026-10-21T08:30:00.000Z",
                "job_state": None,
                "job_started_at": None,
                "job_web_url": None,
            },
        ],
    )

  @patch("collect_infra_metrics.BuildkiteClient")
  def test_get_org_metrics_returns_stats_and_agent_rows_with_same_timestamp(self, mock_bk_cls):
    mock_bk = MagicMock()
    mock_bk_cls.return_value = mock_bk
    mock_bk.get_agents.return_value = [
        {
            "id": "agent-1",
            "name": "bk-docker-1",
            "hostname": "bk-docker-1",
            "connection_state": "connected",
            "paused": False,
            "paused_at": None,
            "connected_at": "2026-10-21T10:00:00.000Z",
            "last_job_finished_at": None,
            "meta_data": ["queue=default"],
            "job": None,
        }
    ]
    mock_bk.get_active_builds.return_value = []

    stats_rows, agent_rows = collect_infra_metrics.get_org_metrics(
        "bazel", {("bazel", "linux"): 120}
    )

    self.assertEqual(len(stats_rows), 1)
    self.assertEqual(len(agent_rows), 1)
    self.assertEqual(stats_rows[0]["timestamp"], agent_rows[0]["timestamp"])
    self.assertEqual(agent_rows[0]["name"], "bk-docker-1")
    self.assertEqual(agent_rows[0]["platform"], "linux")

  @patch("collect_infra_metrics.bigquery.Client")
  def test_push_to_bigquery_uses_table_id(self, mock_bq_client_cls):
    mock_client = MagicMock()
    mock_bq_client_cls.return_value = mock_client
    mock_client.insert_rows_json.return_value = []

    rows = [{"timestamp": "2026-10-21T10:00:00", "org": "bazel"}]
    collect_infra_metrics.push_to_bigquery(rows, 3, collect_infra_metrics.AGENT_SNAPSHOTS_TABLE_ID)

    mock_client.insert_rows_json.assert_called_once_with(
        "bazel-untrusted.bazel_ci_metrics.agent_snapshots", rows
    )


if __name__ == "__main__":
  unittest.main()
