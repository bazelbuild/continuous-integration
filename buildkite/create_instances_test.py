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

import io
import unittest
from unittest.mock import MagicMock, call, patch

import create_instances


class CreateInstanceGroupTest(unittest.TestCase):

    def _regional_config(self):
        return {
            "name": "bk-windows",
            "count": 60,
            "project": "bazel-untrusted",
            "region": "us-central1",
            "target_distribution_shape": "ANY",
            "health_check": "buildkite-check",
            "initial_delay": 60,
            "machine_type": "c2-standard-30",
        }

    @patch("gcloud.create_instance_group")
    @patch("gcloud.create_instance_template")
    @patch("gcloud.delete_instance_group")
    def test_regional_group_skips_zonal_delete_when_regional_exists(
        self, mock_delete, mock_create_template, mock_create_group
    ):
        mock_delete.return_value = MagicMock(returncode=0)
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            rc = create_instances.create_instance_group(self._regional_config())

        self.assertEqual(rc, 0)
        mock_delete.assert_called_once_with(
            "bk-windows", project="bazel-untrusted", region="us-central1"
        )
        mock_create_template.assert_called_once()
        mock_create_group.assert_called_once()
        self.assertEqual(
            mock_create_group.call_args.kwargs["target_distribution_shape"], "ANY"
        )
        self.assertIn("Deleted existing instance group: bk-windows", stdout.getvalue())

    @patch("gcloud.create_instance_group")
    @patch("gcloud.create_instance_template")
    @patch("gcloud.delete_instance_group")
    def test_regional_group_deletes_legacy_zonal_group_when_regional_missing(
        self, mock_delete, mock_create_template, mock_create_group
    ):
        def delete_side_effect(name, project, region=None, zone=None):
            if region == "us-central1":
                return MagicMock(returncode=1)
            if zone == "us-central1-c":
                return MagicMock(returncode=0)
            return MagicMock(returncode=1)

        mock_delete.side_effect = delete_side_effect
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            rc = create_instances.create_instance_group(self._regional_config())

        self.assertEqual(rc, 0)
        self.assertEqual(
            mock_delete.call_args_list,
            [
                call("bk-windows", project="bazel-untrusted", region="us-central1"),
                call("bk-windows", project="bazel-untrusted", zone="us-central1-c"),
            ],
        )
        mock_create_template.assert_called_once()
        mock_create_group.assert_called_once()
        self.assertIn(
            "Deleted legacy zonal instance group in us-central1-c: bk-windows",
            stdout.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
