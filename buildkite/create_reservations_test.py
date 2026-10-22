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
import subprocess
import unittest
from unittest.mock import patch

import create_reservations
import gcloud


def make_existing_reservation(
    name="bk-pilot-c4a-us-central1-b",
    machine_type="c4a-standard-8",
    count=7,
):
    return {
        "name": name,
        "specificReservation": {
            "count": str(count),
            "assuredCount": str(count),
            "inUseCount": str(count),
            "instanceProperties": {
                "machineType": machine_type,
            },
        },
        "specificReservationRequired": False,
        "status": "READY",
    }


class CreateReservationsTest(unittest.TestCase):

    @patch("gcloud.update_reservation")
    @patch("gcloud.create_reservation")
    @patch("gcloud.describe_reservation")
    def test_create_when_missing(self, mock_describe, mock_create, mock_update):
        mock_describe.return_value = None
        config = {
            "name": "bk-pilot-c4a-us-central1-b",
            "project": "bazel-untrusted",
            "zone": "us-central1-b",
            "machine_type": "c4a-standard-8",
            "count": 7,
            "description_prefix": "Bazel CI",
            "description": "untrusted arm64",
        }

        result = create_reservations.reconcile_reservation(config)

        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["action"], "created")
        self.assertEqual(result["current_count"], "-")
        self.assertEqual(result["desired_count"], "7")
        mock_describe.assert_called_once_with(
            "bk-pilot-c4a-us-central1-b",
            project="bazel-untrusted",
            zone="us-central1-b",
        )
        mock_create.assert_called_once_with(
            "bk-pilot-c4a-us-central1-b",
            project="bazel-untrusted",
            zone="us-central1-b",
            machine_type="c4a-standard-8",
            vm_count=7,
            description="Bazel CI: untrusted arm64",
        )
        mock_update.assert_not_called()

    @patch("gcloud.update_reservation")
    @patch("gcloud.create_reservation")
    @patch("gcloud.describe_reservation")
    def test_update_when_count_differs(self, mock_describe, mock_create, mock_update):
        mock_describe.return_value = make_existing_reservation(
            name="bk-pilot-c4a-us-central1-b",
            machine_type="c4a-standard-8",
            count=7,
        )
        config = {
            "name": "bk-pilot-c4a-us-central1-b",
            "project": "bazel-untrusted",
            "zone": "us-central1-b",
            "machine_type": "c4a-standard-8",
            "count": 16,
        }

        result = create_reservations.reconcile_reservation(config)

        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["action"], "updated (7 -> 16)")
        self.assertEqual(result["current_count"], "7")
        self.assertEqual(result["desired_count"], "16")
        mock_create.assert_not_called()
        mock_update.assert_called_once_with(
            "bk-pilot-c4a-us-central1-b",
            project="bazel-untrusted",
            zone="us-central1-b",
            vm_count=16,
        )

    @patch("gcloud.update_reservation")
    @patch("gcloud.create_reservation")
    @patch("gcloud.describe_reservation")
    def test_noop_when_equal(self, mock_describe, mock_create, mock_update):
        mock_describe.return_value = make_existing_reservation(
            name="bk-pilot-c4a-us-central1-b",
            machine_type="c4a-standard-8",
            count=7,
        )
        config = {
            "name": "bk-pilot-c4a-us-central1-b",
            "project": "bazel-untrusted",
            "zone": "us-central1-b",
            "machine_type": "c4a-standard-8",
            "count": 7,
        }

        result = create_reservations.reconcile_reservation(config)

        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["action"], "no-op")
        self.assertEqual(result["current_count"], "7")
        self.assertEqual(result["desired_count"], "7")
        mock_create.assert_not_called()
        mock_update.assert_not_called()

    @patch("gcloud.update_reservation")
    @patch("gcloud.create_reservation")
    @patch("gcloud.describe_reservation")
    def test_error_on_machine_type_mismatch(self, mock_describe, mock_create, mock_update):
        mock_describe.return_value = make_existing_reservation(
            name="bk-c3d-us-central1-c",
            machine_type="c2-standard-30",
            count=60,
        )
        config = {
            "name": "bk-c3d-us-central1-c",
            "project": "bazel-untrusted",
            "zone": "us-central1-c",
            "machine_type": "c3d-standard-30",
            "count": 60,
        }

        stderr_buf = io.StringIO()
        with patch("sys.stderr", stderr_buf):
            result = create_reservations.reconcile_reservation(config)

        self.assertEqual(result["returncode"], 1)
        self.assertEqual(result["action"], "error")
        self.assertIn("c2-standard-30", stderr_buf.getvalue())
        self.assertIn("c3d-standard-30", stderr_buf.getvalue())
        self.assertIn("delete and recreate it manually", stderr_buf.getvalue())
        mock_create.assert_not_called()
        mock_update.assert_not_called()

    @patch("gcloud.update_reservation")
    @patch("gcloud.create_reservation")
    @patch("gcloud.describe_reservation")
    def test_dry_run_prints_commands_without_mutating(
        self, mock_describe, mock_create, mock_update
    ):
        # 1. Missing reservation in dry-run mode
        mock_describe.return_value = None
        create_cfg = {
            "name": "bk-c3d-us-central1-a",
            "project": "bazel-untrusted",
            "zone": "us-central1-a",
            "machine_type": "c3d-standard-30",
            "count": 60,
        }
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            res_create = create_reservations.reconcile_reservation(create_cfg, dry_run=True)

        self.assertEqual(res_create["returncode"], 0)
        self.assertEqual(res_create["action"], "create (dry-run)")
        self.assertIn(
            "[DRY RUN] gcloud compute reservations create bk-c3d-us-central1-a "
            "--project bazel-untrusted --zone us-central1-a "
            "--machine-type c3d-standard-30 --vm-count 60",
            stdout_buf.getvalue(),
        )

        # 2. Existing reservation with different count in dry-run mode
        mock_describe.return_value = make_existing_reservation(
            name="bk-pilot-c4a-us-central1-b",
            machine_type="c4a-standard-8",
            count=7,
        )
        update_cfg = {
            "name": "bk-pilot-c4a-us-central1-b",
            "project": "bazel-untrusted",
            "zone": "us-central1-b",
            "machine_type": "c4a-standard-8",
            "count": 16,
        }
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            res_update = create_reservations.reconcile_reservation(update_cfg, dry_run=True)

        self.assertEqual(res_update["returncode"], 0)
        self.assertEqual(res_update["action"], "update 7 -> 16 (dry-run)")
        self.assertIn(
            "[DRY RUN] gcloud compute reservations update bk-pilot-c4a-us-central1-b "
            "--project bazel-untrusted --zone us-central1-b --vm-count 16",
            stdout_buf.getvalue(),
        )

        mock_create.assert_not_called()
        mock_update.assert_not_called()

    @patch("gcloud.gcloud")
    def test_describe_reservation_returns_none_when_not_found(self, mock_gcloud):
        mock_gcloud.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["gcloud", "compute", "reservations", "describe"],
            stderr=(
                "ERROR: (gcloud.compute.reservations.describe) HTTPError 404: "
                "The resource 'projects/bazel-untrusted/zones/us-central1-b/"
                "reservations/missing' was not found."
            ),
        )
        self.assertIsNone(
            gcloud.describe_reservation("missing", project="bazel-untrusted", zone="us-central1-b")
        )

    @patch("create_reservations.read_config_file")
    def test_main_unknown_name_returns_error(self, mock_read_config):
        mock_read_config.return_value = {
            "default_reservation": {},
            "reservations": [
                {
                    "name": "bk-pilot-c4a-us-central1-b",
                    "project": "bazel-untrusted",
                    "zone": "us-central1-b",
                    "machine_type": "c4a-standard-8",
                    "count": 7,
                }
            ],
        }
        rc = create_reservations.main(["nonexistent-name"])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
