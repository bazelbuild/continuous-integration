#!/usr/bin/env python3
#
# Copyright 2026 The Bazel Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_image

FULL_SHA = "d7c72072aa237a1e92dd445449a4525886c90222"


def _make_build(number, state, jobs, commit=FULL_SHA, branch="master", env=None):
    return {
        "number": number, "state": state, "commit": commit, "branch": branch,
        "env": env or {"FOO": "bar"}, "jobs": jobs,
        "web_url": f"https://buildkite.com/bazel-testing/test/builds/{number}",
    }


def _make_job(job_id, name, state, soft_failed=False, raw_log_url=None):
    return {
        "id": job_id, "type": "script", "name": name, "state": state,
        "soft_failed": soft_failed, "raw_log_url": raw_log_url,
        "web_url": f"https://buildkite.com/bazel-testing/test/builds/1#{job_id}",
    }


class ValidateImageTest(unittest.TestCase):

    def test_to_pipeline_slug(self):
        self.assertEqual(validate_image.to_pipeline_slug("Bazel :bazel:"), "bazel-bazel")
        self.assertEqual(
            validate_image.to_pipeline_slug("Bazel :bazel: Github Presubmit"),
            "bazel-bazel-github-presubmit",
        )
        self.assertEqual(
            validate_image.to_pipeline_slug("Google Bazel Presubmit"), "google-bazel-presubmit"
        )

    @mock.patch.dict(os.environ, {}, clear=True)
    @mock.patch("bazelci.execute_command_and_get_output", return_value="bkua_secret_token\n")
    def test_get_buildkite_token_from_secret_manager(self, mock_exec):
        self.assertEqual(validate_image.get_buildkite_token("bazel-testing"), "bkua_secret_token")
        args = mock_exec.call_args[0][0]
        self.assertIn("--secret=bazel-testing-image-validation-buildkite-token", args)
        self.assertIn("--project=bazel-public", args)

    def test_find_baseline_requires_full_40_char_sha(self):
        client = mock.MagicMock()
        short_sha = _make_build(11, "passed", [], commit="d7c72072aa2")
        head_build = _make_build(10, "passed", [], commit="HEAD")
        full_sha = _make_build(9, "passed", [], commit=FULL_SHA)
        client.get_build_info_list.side_effect = [[], [short_sha, head_build, full_sha]]
        self.assertEqual(validate_image.find_baseline_build(client, "bazel-bazel")["number"], 9)
        self.assertEqual(client.get_build_info_list.call_count, 2)

        client.reset_mock()
        client.get_build_info_list.side_effect = [[short_sha, full_sha]]
        self.assertEqual(
            validate_image.find_baseline_build(client, "google-bazel-presubmit")["number"], 9
        )

    @mock.patch.dict(os.environ, {"BUILDKITE_API_TOKEN": "tok", "BUILDKITE_BUILD_ID": "b1"})
    @mock.patch("bazelci.execute_command")
    @mock.patch("bazelci.BuildkiteClient")
    def test_flake_guard_retries_once_and_passes(self, mock_client_cls, mock_exec):
        client = mock_client_cls.return_value
        j1_pass = _make_job("j1", ":ubuntu: 22.04", "passed")
        j2_pass = _make_job("j2", ":windows:", "passed")
        j2_fail = _make_job("j2", ":windows:", "failed")
        baseline = _make_build(
            100, "passed", [j1_pass, j2_pass], FULL_SHA, "master", {"USE_BAZEL_DIFF": "1"}
        )
        client.get_build_info_list.return_value = [baseline]
        client.trigger_new_build.return_value = _make_build(101, "scheduled", [])
        client.get_build_info.side_effect = [
            _make_build(101, "failed", [j1_pass, j2_fail]),
            _make_build(101, "passed", [j1_pass, j2_pass]),
        ]
        rc = validate_image.main(
            ["--org=bazel-testing", "--pipelines=Google Bazel Presubmit", "--poll_interval=0"]
        )
        self.assertEqual(rc, 0)
        client.trigger_new_build.assert_called_once_with(
            commit=FULL_SHA,
            message="Validate VM image (baseline build #100)",
            env={"USE_BAZEL_DIFF": "1"},
            branch="master",
        )
        client.trigger_job_retry.assert_called_once_with(101, "j2")
        annotate_args = mock_exec.call_args[0][0]
        self.assertIn("--style=warning", annotate_args)
        self.assertIn("Flaky Jobs (Passed on Retry)", annotate_args[-1])

    @mock.patch.dict(os.environ, {"BUILDKITE_API_TOKEN": "tok", "BUILDKITE_BUILD_ID": "b1"})
    @mock.patch("bazelci.execute_command")
    @mock.patch("bazelci.BuildkiteClient")
    def test_regression_exits_nonzero_after_retry(self, mock_client_cls, mock_exec):
        client = mock_client_cls.return_value
        baseline = _make_build(100, "passed", [_make_job("j1", ":ubuntu: 22.04", "passed")])
        failed_job = _make_job("j1", ":ubuntu: 22.04", "failed", raw_log_url="https://log")
        client.get_build_info_list.return_value = [baseline]
        client.trigger_new_build.return_value = _make_build(101, "scheduled", [])
        client.get_build_info.side_effect = [
            _make_build(101, "failed", [failed_job]),
            _make_build(101, "failed", [failed_job]),
        ]
        client.get_build_log.return_value = "line 1\nERROR: docker not found\n"
        rc = validate_image.main(
            ["--org=bazel-testing", "--pipelines=Bazel :bazel:", "--poll_interval=0"]
        )
        self.assertEqual(rc, 1)
        client.trigger_job_retry.assert_called_once_with(101, "j1")
        annotate_args = mock_exec.call_args[0][0]
        self.assertIn("--style=error", annotate_args)
        self.assertIn("ERROR: docker not found", annotate_args[-1])

    @mock.patch.dict(os.environ, {"BUILDKITE_API_TOKEN": "tok", "BUILDKITE_BUILD_ID": "b1"})
    @mock.patch("bazelci.execute_command")
    @mock.patch("bazelci.BuildkiteClient")
    def test_timeout_exits_nonzero(self, mock_client_cls, mock_exec):
        client = mock_client_cls.return_value
        client.get_build_info_list.return_value = [
            _make_build(100, "passed", [_make_job("j1", ":ubuntu: 22.04", "passed")])
        ]
        running = _make_build(101, "running", [_make_job("j1", ":ubuntu: 22.04", "running")])
        client.trigger_new_build.return_value = running
        client.get_build_info.return_value = running
        rc = validate_image.main(
            ["--org=bazel-testing", "--pipelines=Bazel :bazel:", "--timeout=0", "--poll_interval=0"]
        )
        self.assertEqual(rc, 1)
        self.assertIn("timed out", mock_exec.call_args[0][0][-1])


if __name__ == "__main__":
    unittest.main()
