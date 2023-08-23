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

os.environ["BUILDKITE_ORGANIZATION_SLUG"] = "bazel"
os.environ["BUILDKITE_PIPELINE_SLUG"] = "test"

import bazelci
import unittest
import yaml


class CalculateFlags(unittest.TestCase):
    _CONFIGS = yaml.safe_load(
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

    def test_basic_functionality(self):
        tasks = self._CONFIGS.get("tasks")
        flags, json_profile_out, capture_corrupted_outputs_dir = bazelci.calculate_flags(
            tasks.get("basic"), "build_flags", "build", "/tmp", ["HOME"]
        )
        self.assertEqual(flags, ["--enable_x", "--enable_y", "--test_env=HOME"])
        self.assertEqual(json_profile_out, None)
        self.assertEqual(capture_corrupted_outputs_dir, None)

    def test_json_profile(self):
        tasks = self._CONFIGS.get("tasks")
        flags, json_profile_out, capture_corrupted_outputs_dir = bazelci.calculate_flags(
            tasks.get("json_profile"), "build_flags", "build", "/tmp", ["HOME"]
        )
        self.assertEqual(
            flags,
            ["--enable_x", "--enable_y", "--profile=/tmp/build.profile.gz", "--test_env=HOME"],
        )
        self.assertEqual(json_profile_out, "/tmp/build.profile.gz")

    def test_capture_corrupted(self):
        tasks = self._CONFIGS.get("tasks")
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

    def test_no_flags_in_config(self):
        tasks = self._CONFIGS.get("tasks")
        flags, json_profile_out, capture_corrupted_outputs_dir = bazelci.calculate_flags(
            tasks.get("no_flags"), "build_flags", "build", "/tmp", ["HOME"]
        )
        self.assertEqual(flags, ["--test_env=HOME"])

    def test_merge_flags(self):
        tasks = self._CONFIGS.get("tasks")
        flags, json_profile_out, capture_corrupted_outputs_dir = bazelci.calculate_flags(
            tasks.get("merge_flags"), "build_flags", "build", "/tmp", ["HOME"]
        )
        self.assertEqual(
            flags,
            ["--enable_a", "--enable_b", "--enable_z", "--enable_w", "--test_env=HOME"],
        )


class CalculateTargets(unittest.TestCase):
    _CONFIGS = yaml.safe_load(
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

    def test_basic_functionality(self):
        tasks = self._CONFIGS.get("tasks")
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

    def test_merge(self):
        tasks = self._CONFIGS.get("tasks")
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


if __name__ == "__main__":
    unittest.main()
