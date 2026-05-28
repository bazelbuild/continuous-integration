import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import json
import tempfile
import base64

from buildkite import collect_metrics


def create_mock_bep_content(test_results=None, exit_code=0):
    content = []
    
    # 1. Optional Test Results
    if test_results:
        for tr in test_results:
            content.append(json.dumps({
                "id": {"testResult": {"label": tr["label"]}},
                "testResult": {"status": tr["status"], "testAttemptDurationMillis": str(tr["duration_ms"])},
            }))
            
    # 2. Common Build Metrics
    content.append(json.dumps({
        "id": {"buildMetrics": {}},
        "buildMetrics": {
            "timingMetrics": {"wallTimeInMs": "10000"},
            "actionSummary": {
                "actionsExecuted": "100",
                "runnerCount": [{"name": "remote cache hit", "count": "50"}],
            },
            "artifactMetrics": {"topLevelArtifacts": {"sizeInBytes": "1024"}},
            "networkMetrics": {"systemNetworkStats": {"bytesRecv": "512"}},
        },
    }))
    
    # 3. Common Build Tool Logs (Critical Path)
    content.append(json.dumps({
        "id": {"buildToolLogs": {}},
        "buildToolLogs": {
            "log": [{
                "name": "critical path",
                "contents": base64.b64encode(b"Critical Path: 15.0s\n").decode("utf-8"),
            }]
        },
    }))
    
    # 4. Common Build Finished
    content.append(json.dumps({
        "id": {"buildFinished": {}},
        "finished": {"exitCode": {"code": exit_code}}
    }))
    
    return content


class TestPublishMetrics(unittest.TestCase):

    def setUp(self):
        # Reset environment variables before each test
        self.original_environ = os.environ.copy()
        os.environ.clear()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original_environ)

    # --- Test 1: Git Stats Logic ---
    @patch("subprocess.check_output")
    def test_get_git_stats_success(self, mock_subprocess):
        # Mock successful git output
        mock_subprocess.return_value = " 5 files changed, 20 insertions(+), 5 deletions(-)"

        count = collect_metrics.get_git_stats()
        self.assertEqual(count, 5)

    @patch("subprocess.check_output")
    def test_get_git_stats_singular(self, mock_subprocess):
        # Mock singular output
        mock_subprocess.return_value = " 1 file changed, 1 insertion(+)"

        count = collect_metrics.get_git_stats()
        self.assertEqual(count, 1)

    @patch("subprocess.check_output")
    def test_get_git_stats_failure(self, mock_subprocess):
        # Mock a git failure
        mock_subprocess.side_effect = Exception("Git command not found")

        count = collect_metrics.get_git_stats()
        self.assertEqual(count, 9999)  # Fallback value

    # --- Test 2: BEP Parsing ---
    def test_parse_bep_valid(self):
        # Create a mock BEP file content
        test_results = [
            {"label": "//pkg:test1", "status": "PASSED", "duration_ms": 1500},
            {"label": "//pkg:test2", "status": "FAILED", "duration_ms": 5000},
        ]
        mock_bep_content = create_mock_bep_content(test_results=test_results)

        # Create a temp file to hold the data
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
            tf.write("\n".join(mock_bep_content))
            temp_path = tf.name

        try:
            bep_metrics = collect_metrics.parse_bep(temp_path)

            # Verify Metrics
            self.assertEqual(bep_metrics.wall_time_ms, 10000)
            self.assertEqual(bep_metrics.total_actions, 100)
            self.assertEqual(bep_metrics.remote_and_disk_cache_hits, 50)
            self.assertEqual(bep_metrics.failed_test_count, 1)
            self.assertEqual(bep_metrics.critical_path_s, 15.0)
            self.assertEqual(bep_metrics.exit_code, 0)

            # Verify Targets
            self.assertEqual(len(bep_metrics.targets), 2)
            target1 = next(t for t in bep_metrics.targets if t.label == "//pkg:test1")
            self.assertEqual(target1.status, "PASSED")
            self.assertEqual(target1.duration_s, 1.5)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        # --- Second Run to fall back to outputArtifactsSeen ---
        mock_bep_content_2 = [
            json.dumps(
                {
                    "id": {"buildMetrics": {}},
                    "buildMetrics": {
                        "artifactMetrics": {
                            "topLevelArtifacts": {"sizeInBytes": "0"},
                            "outputArtifactsSeen": {"sizeInBytes": "4096"}
                        },
                    },
                }
            ),
        ]
        
        # Create a temp file to hold the data
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf2:
            tf2.write("\n".join(mock_bep_content_2))
            temp_path_2 = tf2.name
            
        try:
            bep_metrics_2 = collect_metrics.parse_bep(temp_path_2)
            self.assertEqual(bep_metrics_2.output_size_bytes, 4096)
        finally:
            if os.path.exists(temp_path_2):
                os.remove(temp_path_2)

    def test_parse_bep_build_only(self):
        # Create a mock BEP file content with only build metrics
        mock_bep_content = create_mock_bep_content()

        # Create a temp file to hold the data
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
            tf.write("\n".join(mock_bep_content))
            temp_path = tf.name

        try:
            bep_metrics = collect_metrics.parse_bep(temp_path)

            # Verify Metrics
            self.assertEqual(bep_metrics.wall_time_ms, 10000)
            self.assertEqual(bep_metrics.total_actions, 100)
            self.assertEqual(bep_metrics.remote_and_disk_cache_hits, 50)
            self.assertEqual(bep_metrics.failed_test_count, 0)
            self.assertEqual(bep_metrics.critical_path_s, 15.0)
            self.assertEqual(bep_metrics.exit_code, 0)

            # Verify Targets are empty
            self.assertEqual(len(bep_metrics.targets), 0)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_extract_critical_path(self):
        # Mock a Base64 encoded critical path log
        raw_log = "Critical Path: 12.5s\n  Action A..."
        b64_log = base64.b64encode(raw_log.encode("utf-8")).decode("utf-8")

        logs = [{"name": "critical path", "contents": b64_log}]
        duration = collect_metrics.extract_critical_path(logs)

        self.assertEqual(duration, 12.5)

    # --- Test 3: Main Logic & BigQuery Push ---
    @patch("buildkite.collect_metrics.subprocess.run")
    def test_publish_to_bigquery(self, mock_run):
        # Mock the subprocess run to succeed (return code 0)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        test_row = {"build_number": 123, "pipeline": "test"}
        collect_metrics.publish_to_bigquery(test_row)

        # Verify it called subprocess.run with bq insert
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        self.assertTrue(any("bq" in arg for arg in call_args))
        self.assertIn("insert", call_args)

    @patch("buildkite.collect_metrics.publish_to_bigquery")
    @patch("buildkite.collect_metrics.parse_bep")
    @patch("buildkite.collect_metrics.get_git_stats")
    def test_collect_metrics_end_to_end(self, mock_git, mock_parse, mock_publish):
        # Setup Environment
        os.environ["BUILDKITE_BUILD_NUMBER"] = "500"
        os.environ["BUILDKITE_PIPELINE_SLUG"] = "test-pipeline"
        os.environ["BUILDKITE_ORGANIZATION_SLUG"] = "test-org"

        # Setup Mocks
        mock_git.return_value = 5  # 5 changed files

        # Mock BEP Return
        mock_bep_metrics = collect_metrics.BazelMetrics(
            wall_time_ms=5000,
            critical_path_s=4.0,
            remote_and_disk_cache_hits=10,
            total_actions=20,
            output_size_bytes=100,
            bytes_downloaded=50,
            failed_test_count=0,
            exit_code=0,
        )
        mock_parse.return_value = mock_bep_metrics

        # Run Function (with mocked timestamps)
        with patch("buildkite.collect_metrics.fetch_job_timestamps") as mock_fetch:
            mock_fetch.return_value = collect_metrics.JobTimestamps(
                created_at="2023-10-25T10:00:00Z",
                started_at="2023-10-25T10:05:00Z"
            )
            collect_metrics.collect_metrics_and_push_to_bigquery(test_bep_path="dummy_path.json")

        # Verify publish_to_bigquery was called
        mock_publish.assert_called_once()

        # Inspect the row payload that was generated
        row = mock_publish.call_args[0][0]

        self.assertEqual(row["build_number"], 500)
        self.assertEqual(row["pipeline"], "test-pipeline")
        self.assertEqual(row["org"], "test-org")
        self.assertEqual(row["changed_files_count"], 5)
        self.assertEqual(row["test"]["failed_test_count"], 0)
        self.assertEqual(row.get("queue_duration_s"), 300.0)

    @patch("buildkite.collect_metrics.publish_to_bigquery")
    @patch("buildkite.collect_metrics.parse_bep")
    @patch("buildkite.collect_metrics.get_git_stats")
    def test_collect_metrics_combined(self, mock_git, mock_parse, mock_publish):
        # Setup Environment
        os.environ["BUILDKITE_BUILD_NUMBER"] = "500"
        os.environ["BUILDKITE_PIPELINE_SLUG"] = "test-pipeline"
        os.environ["BUILDKITE_ORGANIZATION_SLUG"] = "test-org"

        # Setup Mocks
        mock_git.return_value = 5

        # Mock BEP Return based on filename
        def parse_bep_side_effect(filepath):
            if "build" in filepath:
                return collect_metrics.BazelMetrics(
                    wall_time_ms=5000,
                    critical_path_s=4.0,
                    total_actions=20,
                    exit_code=0,
                )
            elif "test" in filepath:
                return collect_metrics.BazelMetrics(
                    wall_time_ms=10000,
                    critical_path_s=8.0,
                    total_actions=50,
                    exit_code=0,
                    failed_test_count=1,
                    targets=[collect_metrics.TestTarget(label="//pkg:test1", status="FAILED", duration_s=5.0)],
                )
            return None

        mock_parse.side_effect = parse_bep_side_effect

        # Run Function
        with patch("buildkite.collect_metrics.fetch_job_timestamps") as mock_fetch:
            mock_fetch.return_value = collect_metrics.JobTimestamps(
                created_at="2023-10-25T10:00:00Z",
                started_at="2023-10-25T10:05:00Z",
                finished_at="2023-10-25T10:15:00Z"
            )
            collect_metrics.collect_metrics_and_push_to_bigquery(
                build_bep_path="build_bep.json", test_bep_path="test_bep.json"
            )

        # Verify publish_to_bigquery was called
        mock_publish.assert_called_once()

        # Inspect the row payload
        row = mock_publish.call_args[0][0]

        self.assertEqual(row["build_number"], 500)
        self.assertIn("build", row)
        self.assertIn("test", row)
        
        self.assertEqual(row["build"]["wall_time_s"], 5.0)
        self.assertEqual(row["test"]["wall_time_s"], 10.0)
        self.assertEqual(row["test"]["failed_test_count"], 1)
        self.assertEqual(len(row["test"]["targets"]), 1)
        self.assertEqual(row["test"]["targets"][0]["label"], "//pkg:test1")

    @patch("buildkite.collect_metrics.subprocess.run")
    def test_publish_to_bigquery_failure(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "out"
        mock_result.stderr = "err"
        mock_run.return_value = mock_result
        
        with patch("buildkite.collect_metrics.print_and_annotate_warning") as mock_annotate:
            collect_metrics.publish_to_bigquery({"test": 1})
            mock_annotate.assert_called_once()

    def test_duration_parsing_error(self):
        with patch.dict(os.environ, {"CHECKOUT_DURATION_S": "invalid", "PREP_DURATION_S": "invalid", "BUILDKITE_BUILD_NUMBER": "500"}):
            with patch("buildkite.collect_metrics.parse_bep") as mock_parse, \
                 patch("buildkite.collect_metrics.publish_to_bigquery"):
                mock_parse.return_value = MagicMock()
                collect_metrics.collect_metrics_and_push_to_bigquery("dummy")

    @patch("buildkite.collect_metrics.parse_bep")
    def test_collect_metrics_bep_failure(self, mock_parse):
        mock_parse.return_value = None
        with patch.dict(os.environ, {"BUILDKITE_BUILD_NUMBER": "500"}):
            with patch("buildkite.collect_metrics.print_and_annotate_warning") as mock_annotate:
                collect_metrics.collect_metrics_and_push_to_bigquery("dummy")
                mock_annotate.assert_called_once_with("Skipping BigQuery push due to missing or failed BEP parsing.")


    def test_parse_bep_file_not_found(self):
        with patch("os.path.exists", return_value=False):
            bep_metrics = collect_metrics.parse_bep("non_existent_file.json")
            self.assertIsNone(bep_metrics)


    @patch("buildkite.collect_metrics.bazelci.BuildkiteClient")
    def test_fetch_job_timestamps_success(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.get_build_info.return_value = {
            "jobs": [{"id": "123", "created_at": "C", "started_at": "S", "finished_at": "F"}]
        }
        
        ts = collect_metrics.fetch_job_timestamps("org", "pipe", 1, "123")
        self.assertEqual(ts.created_at, "C")
        self.assertEqual(ts.finished_at, "F")


if __name__ == "__main__":
    unittest.main()
