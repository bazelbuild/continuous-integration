import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import poll_buildkite

class TestPollBuildkite(unittest.TestCase):

  @patch('poll_buildkite.datetime')
  def test_get_buildkite_metrics(self, mock_datetime, MockClientClass):
    # Mock time
    mock_now = datetime(2023, 1, 1, 12, 0, 0)
    mock_datetime.utcnow.return_value = mock_now

    # Mock Agents Data
    mock_agents = [
        { #busy
            "job": {"id": "job1"},
            "connection_state": "connected",
            "created_at": "2023-01-01T10:00:00Z"
        },
        { #idle
            "job": None,
            "connection_state": "connected",
            "created_at": "2023-01-01T10:00:00Z"
        },
        { #disconnected
            "job": None,
            "connection_state": "disconnected",
            "created_at": "2023-01-01T10:00:00Z"
        }
    ]

    # Mock Scheduled Jobs
    mock_builds = [{"id": "build1"}, {"id": "build2"}]

    # Mock Client Instance
    mock_client = MockClientClass.return_value
    mock_client.get_agents.return_value = mock_agents
    mock_client.get_scheduled_jobs.return_value = mock_builds

    metrics = poll_buildkite.get_org_metrics("test-org")

    self.assertEqual(metrics["timestamp"], mock_now.isoformat())
    self.assertEqual(metrics["org"], "test-org")
    self.assertEqual(metrics["total_agents"], 3)
    self.assertEqual(metrics["busy_agents"], 1)
    self.assertEqual(metrics["idle_agents"], 1)
    self.assertEqual(metrics["disconnected_agents"], 1)
    self.assertEqual(metrics["scheduled_jobs"], 2)

  @patch('poll_buildkite.client')
  def test_push_to_bigquery(self, mock_bq_client):
    rows = [{"test": "data", "timestamp": "2023-01-01T12:00:00"}]

    mock_bq_client.insert_rows_json.return_value = [] # Success (no errors)

    poll_buildkite.push_to_bigquery(rows)

    mock_bq_client.insert_rows_json.assert_called_once_with(
        poll_buildkite.table_ref, rows
    )

if __name__ == '__main__':
  unittest.main()