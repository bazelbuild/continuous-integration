import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import poll_buildkite

class TestPollBuildkite(unittest.TestCase):

  @patch('poll_buildkite.requests.get')
  def test_fetch_all_pages_single_page(self, mock_get):
    # Mock a single page response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{"id": "1"}, {"id": "2"}]
    mock_resp.headers = {}
    mock_get.return_value = mock_resp

    # Create client instance with a mocked token to test the private method
    with patch.dict(poll_buildkite.ORG_TOKENS, {"test-org": "mock-token"}):
      client = poll_buildkite.BuildkiteClient("test-org")
      results = client._fetch_all_pages("agents")

    self.assertEqual(len(results), 2)
    self.assertEqual(results[0]["id"], "1")
    mock_get.assert_called_once()

  @patch('poll_buildkite.requests.get')
  def test_fetch_all_pages_pagination(self, mock_get):
    # Mock Page 1
    resp1 = MagicMock()
    resp1.status_code = 200
    resp1.json.return_value = [{"id": "1"}]
    # Link header pointing to next page
    resp1.headers = {"Link": '<http://test-url?page=2>; rel="next"'}

    # Mock Page 2 (Last page)
    resp2 = MagicMock()
    resp2.status_code = 200
    resp2.json.return_value = [{"id": "2"}]
    resp2.headers = {} # No next link

    # Set side_effect to return resp1 then resp2
    mock_get.side_effect = [resp1, resp2]

    with patch.dict(poll_buildkite.ORG_TOKENS, {"test-org": "mock-token"}):
      client = poll_buildkite.BuildkiteClient("test-org")
      results = client._fetch_all_pages("agents")

    self.assertEqual(len(results), 2)
    self.assertEqual(results[0]["id"], "1")
    self.assertEqual(results[1]["id"], "2")
    self.assertEqual(mock_get.call_count, 2)

  @patch('poll_buildkite.BuildkiteClient')
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