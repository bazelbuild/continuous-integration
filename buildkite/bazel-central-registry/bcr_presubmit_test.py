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
import shlex
import sys
import tempfile
import unittest


os.environ["BUILDKITE_ORGANIZATION_SLUG"] = "bazel"
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import bcr_presubmit


class PresubmitJobCommandQuotingTest(unittest.TestCase):
    def _runner_command(self, task_id):
        steps = []
        bcr_presubmit.add_presubmit_jobs(
            "demo",
            "1.0.0",
            {task_id: {"name": "demo task", "platform": "ubuntu2004", "bazel": "latest"}},
            steps,
        )
        return steps[0]["command"][-1]

    def test_task_id_is_shell_quoted(self):
        sentinel = tempfile.mktemp(prefix="bcr-task-injection.")
        self.addCleanup(lambda: os.remove(sentinel) if os.path.exists(sentinel) else None)
        task_id = "linux$(touch${IFS}%s)" % sentinel

        command = self._runner_command(task_id)
        tokens = shlex.split(command)

        self.assertIn("--task=" + task_id, tokens)
        self.assertNotIn("touch", tokens)
        self.assertFalse(os.path.exists(sentinel))

    def test_module_arguments_are_shell_quoted(self):
        task_id = "linux"
        command = self._runner_command(task_id)
        tokens = shlex.split(command)

        self.assertIn("--module_name=demo", tokens)
        self.assertIn("--module_version=1.0.0", tokens)
        self.assertIn("--task=linux", tokens)


if __name__ == "__main__":
    unittest.main()
