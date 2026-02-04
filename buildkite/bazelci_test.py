#!/usr/bin/env python3
#
# Copyright 2023 The Bazel Authors. All rights reserved.
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
from typing import Any, Dict, List, Optional, Tuple

os.environ["BUILDKITE_ORGANIZATION_SLUG"] = "bazel"
os.environ["BUILDKITE_PIPELINE_SLUG"] = "test"

import bazelci
import unittest
import yaml


class CalculateFlags(unittest.TestCase):
    _CONFIGS: Dict[str, Any] = yaml.safe_load(
        """
.base_flags: &base_flags
  ? "--enable_a"
  ? "--enable_b"

tasks:
  basic:
    build_flags:
      - "--enable_x"
      - "--enable_y"
    build_targets:
      - "//..."
  json_profile:
    build_flags:
      - "--enable_x"
      - "--enable_y"
    build_targets:
      - "//..."
    include_json_profile:
      - build
  capture_corrupted:
    build_flags:
      - "--enable_x"
      - "--enable_y"
    build_targets:
      - "//..."
    capture_corrupted_outputs:
      - build
  no_flags:
    test_targets:
      - "//..."
  merge_flags:
    build_flags:
      <<: *base_flags
      ? "--enable_z"
      ? "--enable_w"
    build_targets:
      - "//..."
    """
    )

    def test_basic_functionality(self) -> None:
        tasks = self._CONFIGS.get("tasks", {})
        flags, json_profile_out, capture_corrupted_outputs_dir = bazelci.calculate_flags(
            tasks.get("basic"), "build_flags", "build", "/tmp", ["HOME"]
        )
        self.assertEqual(flags, ["--enable_x", "--enable_y", "--test_env=HOME"])
        self.assertEqual(json_profile_out, None)
        self.assertEqual(capture_corrupted_outputs_dir, None)

    def test_json_profile(self) -> None:
        tasks = self._CONFIGS.get("tasks", {})
        flags, json_profile_out, capture_corrupted_outputs_dir = bazelci.calculate_flags(
            tasks.get("json_profile"), "build_flags", "build", "/tmp", ["HOME"]
        )
        self.assertEqual(
            flags,
            ["--enable_x", "--enable_y", "--profile=/tmp/build.profile.gz", "--test_env=HOME"],
        )
        self.assertEqual(json_profile_out, "/tmp/build.profile.gz")

    def test_capture_corrupted(self) -> None:
        tasks = self._CONFIGS.get("tasks", {})
        flags, json_profile_out, capture_corrupted_outputs_dir = bazelci.calculate_flags(
            tasks.get("capture_corrupted"), "build_flags", "build", "/tmp", ["HOME"]
        )
        self.assertEqual(
            flags,
            [
                "--enable_x",
                "--enable_y",
                "--experimental_remote_capture_corrupted_outputs=/tmp/build_corrupted_outputs",
                "--test_env=HOME",
            ],
        )
        self.assertEqual(capture_corrupted_outputs_dir, "/tmp/build_corrupted_outputs")

    def test_no_flags_in_config(self) -> None:
        tasks = self._CONFIGS.get("tasks", {})
        flags, json_profile_out, capture_corrupted_outputs_dir = bazelci.calculate_flags(
            tasks.get("no_flags"), "build_flags", "build", "/tmp", ["HOME"]
        )
        self.assertEqual(flags, ["--test_env=HOME"])

    def test_merge_flags(self) -> None:
        tasks = self._CONFIGS.get("tasks", {})
        flags, json_profile_out, capture_corrupted_outputs_dir = bazelci.calculate_flags(
            tasks.get("merge_flags"), "build_flags", "build", "/tmp", ["HOME"]
        )
        self.assertEqual(
            flags,
            ["--enable_a", "--enable_b", "--enable_z", "--enable_w", "--test_env=HOME"],
        )


class CalculateTargets(unittest.TestCase):
    _CONFIGS: Dict[str, Any] = yaml.safe_load(
        """
.base_targets: &base_targets
  ? "//..."
  ? "-//experimental/..."

tasks:
  basic:
    build_targets:
      - "//..."
      - "-//bad/..."
  merge:
    build_targets:
      <<: *base_targets
      ? "//experimental/good/..."
    """
    )

    def test_basic_functionality(self) -> None:
        tasks = self._CONFIGS.get("tasks", {})
        build_targets, test_targets, coverage_targets, index_targets = bazelci.calculate_targets(
            tasks.get("basic"),
            "bazel",
            build_only=False,
            test_only=False,
            workspace_dir="/tmp",
            ws_setup_func=None,
            git_commit="abcd",
            test_flags=[],
        )
        self.assertEqual(build_targets, ["//...", "-//bad/..."])
        self.assertEqual(test_targets, [])
        self.assertEqual(coverage_targets, [])
        self.assertEqual(index_targets, [])

    def test_merge(self) -> None:
        tasks = self._CONFIGS.get("tasks", {})
        build_targets, test_targets, coverage_targets, index_targets = bazelci.calculate_targets(
            tasks.get("merge"),
            "bazel",
            build_only=False,
            test_only=False,
            workspace_dir="/tmp",
            ws_setup_func=None,
            git_commit="abcd",
            test_flags=[],
        )
        self.assertEqual(build_targets, ["//...", "-//experimental/...", "//experimental/good/..."])

class MatrixExpansion(unittest.TestCase):
    _CONFIGS: Dict[str, Any] = yaml.safe_load(
        """
matrix:
  bazel: ["1.2.3", "2.3.4"]
  platform: ["pf1", "pf2"]
tasks:
  basic:
    name: "Basic"
  unformatted:
    name: "Unformatted"
    bazel: ${{ bazel }}
  without_name:
    bazel: ${{ bazel }}
  formatted:
    name: "Formatted w/ Bazel v{bazel} on {platform}"
    bazel: ${{ bazel }}
    platform: ${{ platform }}
    """
    )

    def test_basic_functionality(self) -> None:
        config = self._CONFIGS

        bazelci.expand_task_config(config)
        expanded_tasks = config["tasks"]
        self.assertEqual(len(expanded_tasks), 9)
        expanded_task_names = [task.get("name", None) for id, task in expanded_tasks.items()]
        self.assertEqual(expanded_task_names, [
            "Basic", # no matrix expansion
            "Unformatted", # bazel v1.2.3
            "Unformatted",  # bazel v2.3.4
            None, # no name, bazel v1.2.3
            None, # no name, bazel v2.3.4
            "Formatted w/ Bazel v1.2.3 on pf1",
            "Formatted w/ Bazel v1.2.3 on pf2",
            "Formatted w/ Bazel v2.3.4 on pf1",
            "Formatted w/ Bazel v2.3.4 on pf2",
        ])


class MatrixExclude(unittest.TestCase):
    _CONFIGS_SINGLE_EXCLUDE: Dict[str, Any] = yaml.safe_load(
        """
matrix:
  bazel: ["1.2.3", "2.3.4"]
  platform: ["pf1", "pf2"]
  exclude:
    - bazel: "1.2.3"
      platform: "pf2"
tasks:
  formatted:
    name: "Formatted w/ Bazel v{bazel} on {platform}"
    bazel: ${{ bazel }}
    platform: ${{ platform }}
        """
    )

    _CONFIGS_MULTIPLE_EXCLUDES: Dict[str, Any] = yaml.safe_load(
        """
matrix:
  bazel: ["1.2.3", "2.3.4"]
  platform: ["pf1", "pf2"]
  exclude:
    - bazel: "1.2.3"
      platform: "pf2"
    - bazel: "2.3.4"
      platform: "pf1"
tasks:
  formatted:
    name: "Formatted w/ Bazel v{bazel} on {platform}"
    bazel: ${{ bazel }}
    platform: ${{ platform }}
        """
    )

    _CONFIGS_PARTIAL_EXCLUDE: Dict[str, Any] = yaml.safe_load(
        """
matrix:
  bazel: ["1.2.3", "2.3.4"]
  platform: ["pf1", "pf2"]
  exclude:
    - platform: "pf2"
tasks:
  formatted:
    name: "Formatted w/ Bazel v{bazel} on {platform}"
    bazel: ${{ bazel }}
    platform: ${{ platform }}
        """
    )

    def test_single_exclude(self) -> None:
        import copy
        config = copy.deepcopy(self._CONFIGS_SINGLE_EXCLUDE)

        bazelci.expand_task_config(config)
        expanded_tasks = config["tasks"]
        # Total combinations: 2 * 2 = 4, minus 1 excluded = 3
        self.assertEqual(len(expanded_tasks), 3)
        expanded_task_names = [task.get("name", None) for id, task in expanded_tasks.items()]
        self.assertEqual(expanded_task_names, [
            "Formatted w/ Bazel v1.2.3 on pf1",
            "Formatted w/ Bazel v2.3.4 on pf1",
            "Formatted w/ Bazel v2.3.4 on pf2",
        ])

    def test_multiple_excludes(self) -> None:
        import copy
        config = copy.deepcopy(self._CONFIGS_MULTIPLE_EXCLUDES)

        bazelci.expand_task_config(config)
        expanded_tasks = config["tasks"]
        # Total combinations: 2 * 2 = 4, minus 2 excluded = 2
        self.assertEqual(len(expanded_tasks), 2)
        expanded_task_names = [task.get("name", None) for id, task in expanded_tasks.items()]
        self.assertEqual(expanded_task_names, [
            "Formatted w/ Bazel v1.2.3 on pf1",
            "Formatted w/ Bazel v2.3.4 on pf2",
        ])

    def test_partial_attribute_exclude(self) -> None:
        import copy
        config = copy.deepcopy(self._CONFIGS_PARTIAL_EXCLUDE)

        bazelci.expand_task_config(config)
        expanded_tasks = config["tasks"]
        # Total combinations: 2 * 2 = 4, minus 2 excluded (all pf2) = 2
        self.assertEqual(len(expanded_tasks), 2)
        expanded_task_names = [task.get("name", None) for id, task in expanded_tasks.items()]
        self.assertEqual(expanded_task_names, [
            "Formatted w/ Bazel v1.2.3 on pf1",
            "Formatted w/ Bazel v2.3.4 on pf1",
        ])


if __name__ == "__main__":
    unittest.main()
