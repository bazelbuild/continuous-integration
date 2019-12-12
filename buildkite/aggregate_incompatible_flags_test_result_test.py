#!/usr/bin/env python3
#
# Copyright 2019 The Bazel Authors. All rights reserved.
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

import aggregate_incompatible_flags_test_result as code_under_test
import unittest


class GetPipelineAndPlatformTest(unittest.TestCase):

    _DATA = {
        "Bazel (:ubuntu: 18.04 (OpenJDK 11))": ("Bazel", ":ubuntu: 18.04 (OpenJDK 11)"),
        "Bazel (Clang on :ubuntu: 18.04 (OpenJDK 11))": ("Bazel", ":ubuntu: 18.04 (OpenJDK 11)"),
        "Bazel Federation (bazel_skylib on :darwin: (OpenJDK 8))": (
            "Bazel Federation",
            ":darwin: (OpenJDK 8)",
        ),
        "Bazel Examples (Android Firebase Cloud Messaging on :windows: (OpenJDK 8))": (
            "Bazel Examples",
            ":windows: (OpenJDK 8)",
        ),
        "rules_cc (:ubuntu: 18.04 (OpenJDK 11))": ("rules_cc", ":ubuntu: 18.04 (OpenJDK 11)"),
        "rules_jvm_external - examples (Simple example on :darwin: (OpenJDK 8))": (
            "rules_jvm_external",
            ":darwin: (OpenJDK 8)",
        ),
        "Tulsi (:darwin: (OpenJDK 8)) ": ("Tulsi", ":darwin: (OpenJDK 8)"),
        "rules_haskell (:ubuntu: 18.04 (OpenJDK 11)) ": (
            "rules_haskell",
            ":ubuntu: 18.04 (OpenJDK 11)",
        ),
        "Skydoc (:windows: (OpenJDK 8)) ": ("Skydoc", ":windows: (OpenJDK 8)"),
        "Bazel Examples (Bazel end-to-end example on :windows: (OpenJDK 8)) ": (
            "Bazel Examples",
            ":windows: (OpenJDK 8)",
        ),
        "Bazel Federation (bazel_skylib on :ubuntu: 18.04 (OpenJDK 11)) ": (
            "Bazel Federation",
            ":ubuntu: 18.04 (OpenJDK 11)",
        ),
        "Bazel Federation (bazel_skylib on :windows: (OpenJDK 8)) ": (
            "Bazel Federation",
            ":windows: (OpenJDK 8)",
        ),
        "Bazel Federation (examples (Stardoc) on :darwin: (OpenJDK 8)) ": (
            "Bazel Federation",
            ":darwin: (OpenJDK 8)",
        ),
        "Bazel Federation (examples (Stardoc) on :ubuntu: 16.04 (OpenJDK 8)) ": (
            "Bazel Federation",
            ":ubuntu: 16.04 (OpenJDK 8)",
        ),
    }

    def testRealValues(self):
        for job_name, (expected_pipeline, expected_platform) in self._DATA.items():
            pipeline, platform = code_under_test.get_pipeline_and_platform({"name": job_name})
            self.assertEqual(pipeline, expected_pipeline)
            self.assertEqual(platform, expected_platform)


if __name__ == "__main__":
    unittest.main()
