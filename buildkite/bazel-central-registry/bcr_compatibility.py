#!/usr/bin/env python3
#
# Copyright 2024 The Bazel Authors. All rights reserved.
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
# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring
# pylint: disable=unspecified-encoding
# pylint: disable=invalid-name
"""The CI script for BCR Bazel Compatibility Test pipeline."""


import os
import sys
import subprocess
import time

import bazelci
import bcr_presubmit
from bcr_presubmit import BcrPipelineException

REPORT_FLAGS_RESULTS_BCR_URL = "https://raw.githubusercontent.com/bazelbuild/continuous-integration/{}/buildkite/bazel-central-registry/report_flags_results_bcr.py?{}".format(
    bazelci.GITHUB_BRANCH, int(time.time())
)

CI_MACHINE_NUM = {
    "bazel": {
        "default": 100,
        "windows": 30,
        "macos_arm64": 45,
        "macos": 110,
        "arm64": 1,
    },
    "bazel-testing": {
        "default": 30,
        "windows": 4,
        "macos_arm64": 1,
        "macos": 10,
        "arm64": 1,
    },
}[bazelci.BUILDKITE_ORG]

# Default to use only 30% of CI resources for each type of machines.
CI_RESOURCE_PERCENTAGE = int(os.environ.get('CI_RESOURCE_PERCENTAGE', 30))

def fetch_bcr_presubmit_py_command():
    return "curl -s {0} -o bcr_presubmit.py".format(bcr_presubmit.SCRIPT_URL)

def select_modules_from_env_vars():
    """
    Parses MODULE_SELECTIONS and SMOKE_TEST_PERCENTAGE environment variables
    and returns a list of selected module versions.
    """
    MODULE_SELECTIONS = os.environ.get('MODULE_SELECTIONS', '')
    SMOKE_TEST_PERCENTAGE = os.environ.get('SMOKE_TEST_PERCENTAGE', None)

    if not MODULE_SELECTIONS:
        return []

    selections = [s.strip() for s in MODULE_SELECTIONS.split(',') if s.strip()]
    args = [f"--select={s}" for s in selections]
    if SMOKE_TEST_PERCENTAGE:
        args += [f"--random-percentage={SMOKE_TEST_PERCENTAGE}"]
    output = subprocess.check_output(
        ["python3", "./tools/module_selector.py"] + args,
    )
    modules = []
    for line in output.decode("utf-8").split():
        name, version = line.strip().split("@")
        modules.append((name, version))
    return modules


def get_target_modules():
    """
    If the `MODULE_SELECTIONS` and `SMOKE_TEST_PERCENTAGE(S)` are specified, calculate the target modules from those env vars.
    Otherwise, calculate target modules based on changed files from the main branch.
    """
    if "MODULE_SELECTIONS" not in os.environ:
        raise BcrPipelineException("Please set MODULE_SELECTIONS env var to select modules for testing!")

    modules = select_modules_from_env_vars()
    if modules:
        bazelci.print_expanded_group("The following modules are selected:\n\n%s" % "\n".join([f"{name}@{version}" for name, version in modules]))
        return sorted(list(set(modules)))
    else:
        raise BcrPipelineException("MODULE_SELECTIONS env var didn't select any modules!")

def fetch_report_flags_results_bcr_command():
    return "curl -sS {0} -o report_flags_results_bcr.py".format(
        REPORT_FLAGS_RESULTS_BCR_URL
    )

def create_step_for_report_flags_results():
    parts = [
        bazelci.PLATFORMS[bazelci.DEFAULT_PLATFORM]["python"],
        "report_flags_results_bcr.py",
        "--build_number=%s" % os.getenv("BUILDKITE_BUILD_NUMBER"),
    ]
    return [
        {"wait": "~", "continue_on_failure": "true"},
        bazelci.create_step(
            label="Aggregate incompatible flags test result",
            commands=[
                bazelci.fetch_bazelcipy_command(),
                fetch_report_flags_results_bcr_command(),
                " ".join(parts),
            ],
            platform=bazelci.DEFAULT_PLATFORM,
        ),
    ]

def main():
    # Always respect USE_BAZEL_VERSION to override bazel version
    bazel_version = os.environ.get("USE_BAZEL_VERSION")

    modules = get_target_modules()

    pipeline_steps = []
    calc_concurrency = lambda queue : max(1, (CI_RESOURCE_PERCENTAGE * CI_MACHINE_NUM[queue]) // 100)
    for module_name, module_version in modules:
        previous_size = len(pipeline_steps)

        configs = bcr_presubmit.get_anonymous_module_task_config(module_name, module_version, bazel_version)
        bcr_presubmit.add_presubmit_jobs(module_name, module_version, configs.get("tasks", {}), pipeline_steps, calc_concurrency=calc_concurrency)
        configs = bcr_presubmit.get_test_module_task_config(module_name, module_version, bazel_version)
        bcr_presubmit.add_presubmit_jobs(module_name, module_version, configs.get("tasks", {}), pipeline_steps, is_test_module=True, calc_concurrency=calc_concurrency)

        if len(pipeline_steps) == previous_size:
            bcr_presubmit.error("No pipeline steps generated for %s@%s. Please check the configuration." % (module_name, module_version))

    if pipeline_steps:
        # Always wait for approval to proceed
        pipeline_steps = [{"block": "Please review generated jobs before proceeding", "blocked_state": "running"}] + pipeline_steps
        if bazelci.use_bazelisk_migrate():
            pipeline_steps += create_step_for_report_flags_results()

    bcr_presubmit.upload_jobs_to_pipeline(pipeline_steps)


if __name__ == "__main__":
    sys.exit(main())
