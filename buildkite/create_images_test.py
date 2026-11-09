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
import signal
import subprocess
import unittest
from unittest.mock import MagicMock, patch

import create_images
import gcloud_utils


class GcloudUtilsTimeoutTest(unittest.TestCase):

    @patch("gcloud_utils.time.sleep")
    @patch("gcloud_utils.time.monotonic", side_effect=[10.0, 20.0])
    @patch("gcloud.describe_instance")
    def test_wait_for_instance_times_out(self, mock_describe, _mock_monotonic, _mock_sleep):
        mock_describe.return_value = MagicMock(stdout='{"status": "RUNNING"}')
        with self.assertRaises(TimeoutError) as ctx:
            gcloud_utils.wait_for_instance(
                "bk-testing-windows-image-1",
                "bazel-public",
                "us-central1-f",
                "TERMINATED",
                deadline=15.0,
            )
        self.assertIn("TERMINATED", str(ctx.exception))
        self.assertIn("RUNNING", str(ctx.exception))

    @patch("gcloud_utils.time.sleep")
    @patch("gcloud_utils.time.monotonic", side_effect=[10.0, 20.0])
    @patch("gcloud.get_serial_port_output")
    def test_tail_serial_console_times_out_on_retry(
        self, mock_serial, _mock_monotonic, _mock_sleep
    ):
        mock_serial.side_effect = subprocess.CalledProcessError(
            1, ["gcloud"], stderr="Could not fetch serial port output: TIMEOUT"
        )
        with self.assertRaises(TimeoutError):
            gcloud_utils.tail_serial_console(
                "bk-testing-docker-image-1", "bazel-public", "us-central1-f", deadline=15.0
            )


class CreateImagesWorkflowTimeoutTest(unittest.TestCase):

    @patch("gcloud.delete_instance")
    @patch("gcloud.create_image")
    @patch("gcloud_utils.wait_for_instance")
    @patch("gcloud_utils.tail_serial_console", side_effect=TimeoutError("serial console stuck"))
    @patch("create_images.create_instance")
    @patch("create_images.time.monotonic", return_value=100.0)
    def test_workflow_deletes_vm_and_reraises_on_timeout(
        self,
        _mock_monotonic,
        _mock_create_instance,
        mock_tail,
        mock_wait,
        mock_create_image,
        mock_delete_instance,
    ):
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            with self.assertRaises(TimeoutError):
                create_images.workflow(
                    "bk-testing-windows", create_images.IMAGE_CREATION_VMS["bk-testing-windows"]
                )

        expected_deadline = 100.0 + 90 * 60
        self.assertEqual(mock_wait.call_args.kwargs["deadline"], expected_deadline)
        self.assertEqual(mock_tail.call_args.kwargs["deadline"], expected_deadline)
        mock_create_image.assert_not_called()
        mock_delete_instance.assert_called_once()
        self.assertIn("C:/setup-stdout.log", stderr.getvalue())

    @patch("gcloud.delete_instance")
    @patch("gcloud.create_image")
    @patch("gcloud_utils.wait_for_instance")
    @patch(
        "gcloud_utils.tail_serial_console",
        side_effect=lambda *a, **kw: create_images._handle_sigterm(signal.SIGTERM, None),
    )
    @patch("create_images.create_instance")
    @patch("create_images.signal.signal")
    def test_sigterm_deletes_vm_and_exits_nonzero(
        self,
        mock_signal,
        _mock_create_instance,
        _mock_tail,
        _mock_wait,
        mock_create_image,
        mock_delete_instance,
    ):
        with self.assertRaises(SystemExit) as ctx:
            create_images.main(["bk-testing-docker"])

        self.assertEqual(ctx.exception.code, 1)
        mock_signal.assert_any_call(signal.SIGTERM, create_images._handle_sigterm)
        mock_create_image.assert_not_called()
        mock_delete_instance.assert_called_once()


if __name__ == "__main__":
    unittest.main()
