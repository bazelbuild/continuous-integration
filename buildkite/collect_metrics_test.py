import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import json
import base64

import collect_metrics

class TestPublishMetrics(unittest.TestCase):

  def setUp(self):
    # Reset environment variables before each test
    self.original_environ = os.environ.copy()
    os.environ.clear()

  def tearDown(self):
    os.environ.clear()
    os.environ.update(self.original_environ)

  # --- Test 1: Git Stats Logic ---
  @patch('subprocess.check_output')
  def test_get_git_stats_success(self, mock_subprocess):
    # Mock successful git output
    mock_subprocess.return_value = " 5 files changed, 20 insertions(+), 5 deletions(-)"

    count = collect_metrics.get_git_stats()
    self.assertEqual(count, 5)

  @patch('subprocess.check_output')
  def test_get_git_stats_singular(self, mock_subprocess):
    # Mock singular output
    mock_subprocess.return_value = " 1 file changed, 1 insertion(+)"

    count = collect_metrics.get_git_stats()
    self.assertEqual(count, 1)

  @patch('subprocess.check_output')
  def test_get_git_stats_failure(self, mock_subprocess):
    # Mock a git failure
    mock_subprocess.side_effect = Exception("Git command not found")

    count = collect_metrics.get_git_stats()
    self.assertEqual(count, 9999) # Fallback value

  # --- Test 2: BEP Parsing ---
  def test_parse_bep_valid(self):
    # Create a mock BEP file content
    mock_bep_content = [
        # Test Result Event
        json.dumps({
            "id": {"testResult": {"label": "//pkg:test1"}},
            "testResult": {"status": "PASSED", "testAttemptDurationMillis": "1500"}
        }),
        # Another Test Result (Failed)
        json.dumps({
            "id": {"testResult": {"label": "//pkg:test2"}},
            "testResult": {"status": "FAILED", "testAttemptDurationMillis": "5000"}
        }),
        # Build Metrics
        json.dumps({
            "id": {"buildMetrics": {}},
            "buildMetrics": {
                "timingMetrics": {"wallTimeInMs": "10000"},
                "actionSummary": {"actionsExecuted": "100", "runnerCount": [{"name": "remote cache hit", "count": "50"}]},
                "artifactMetrics": {"topLevelArtifacts": {"sizeInBytes": "2048"}},
                "networkMetrics": {"systemNetworkStats": {"bytesRecv": "1024"}}
            }
        })
    ]

    # Mock file reading
    # Mock file reading
    with patch("builtins.open", mock_open(read_data="\n".join(mock_bep_content))):
      metrics, targets = collect_metrics.parse_bep("dummy.json")

      # Verify Metrics
      self.assertEqual(metrics["wall_time_ms"], 10000)
      self.assertEqual(metrics["total_actions"], 100)
      self.assertEqual(metrics["remote_cache_hits"], 50)
      self.assertEqual(metrics["failed_test_count"], 1) # test2 failed

      # Verify Targets
      self.assertEqual(len(targets), 2)
      target1 = next(t for t in targets if t["label"] == "//pkg:test1")
      self.assertEqual(target1["status"], "PASSED")
      self.assertEqual(target1["duration_s"], 1.5)

  def test_extract_critical_path(self):
    # Mock a Base64 encoded critical path log
    raw_log = "Critical Path: 12.5s\n  Action A..."
    b64_log = base64.b64encode(raw_log.encode("utf-8")).decode("utf-8")

    logs = [{"name": "critical path", "contents": b64_log}]
    duration = collect_metrics.extract_critical_path(logs)

    self.assertEqual(duration, 12.5)

  # --- Test 3: Main Logic & BigQuery Push ---
  @patch('collect_metrics.bigquery.Client')
  @patch('collect_metrics.parse_bep')
  @patch('collect_metrics.get_git_stats')
  def test_collect_metrics_end_to_end(self, mock_git, mock_parse, mock_bq_client):
    # Setup Environment
    os.environ['BUILDKITE_BUILD_NUMBER'] = "500"
    os.environ['BUILDKITE_PIPELINE_SLUG'] = "test-pipeline"

    # Setup Mocks
    mock_git.return_value = 5 # 5 changed files

    # Mock BEP Return
    mock_metrics = {
        "wall_time_ms": 5000,
        "critical_path_s": 4.0,
        "remote_cache_hits": 10,
        "total_actions": 20,
        "output_size_bytes": 100,
        "bytes_downloaded": 50,
        "failed_test_count": 0,
        "exit_code": 0
    }
    mock_targets = []
    mock_parse.return_value = (mock_metrics, mock_targets)

    # Mock BigQuery Client
    mock_client_instance = MagicMock()
    mock_bq_client.return_value = mock_client_instance
    mock_client_instance.insert_rows_json.return_value = [] # No errors

    # Run Function
    collect_metrics.collect_metrics_and_push_to_bigquery("dummy_path.json")

    # Verify BigQuery Insert was called
    mock_client_instance.insert_rows_json.assert_called_once()

    # Inspect the row payload
    call_args = mock_client_instance.insert_rows_json.call_args
    rows = call_args[0][1]

    self.assertEqual(rows[0]['build_number'], 500)
    self.assertEqual(rows[0]['pipeline'], "test-pipeline")
    self.assertEqual(rows[0]['changed_files_count'], 5)
    # Check that we passed the raw count, not a classified string
    self.assertEqual(rows[0]['failed_test_count'], 0)

if __name__ == '__main__':
  unittest.main()