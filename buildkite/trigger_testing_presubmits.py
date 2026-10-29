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

from datetime import datetime, timezone
import os
import shutil
import subprocess
import sys
import time

import requests

import bazelci

ORG = "bazel-testing"
POLL_INTERVAL_SECONDS = 60
TERMINAL_BUILD_STATES = frozenset(["passed", "failed", "canceled", "skipped", "not_run"])
LINUX_IMAGE_SKIP_TASKS = (
    "macos",
    "macos_arm64",
    "windows",
    "windows_arm64",
)
WINDOWS_IMAGE_SKIP_TASKS = (
    "rockylinux8",
    "rockylinux8_arm64",
    "fedora39",
    "ubuntu2404",
    "ubuntu2404_clang",
    "ubuntu2204",
    "macos",
    "macos_arm64",
    "rbe_ubuntu2404",
    "docs_ubuntu2404",
)


def select_skip_tasks(test_vm_names):
    names = [n.strip() for n in (test_vm_names or "").split(",") if n.strip()]
    if names and all("docker" in n and "windows" not in n for n in names):
        return LINUX_IMAGE_SKIP_TASKS
    if names and all("windows" in n and "docker" not in n for n in names):
        return WINDOWS_IMAGE_SKIP_TASKS
    bazelci.eprint(
        f"Warning: cannot infer single target platform from BAZEL_TEST_VM_NAMES={test_vm_names!r}; "
        "running all presubmit tasks without CI_SKIP_TASKS."
    )
    return ()


def is_build_finished(build_info):
    return build_info.get("state") in TERMINAL_BUILD_STATES or bool(build_info.get("finished_at"))


def annotate(context, style, message):
    if not shutil.which("buildkite-agent"):
        return
    bazelci.execute_command(
        [
            "buildkite-agent",
            "annotate",
            f"--style={style}",
            f"--context={context}",
            message,
        ],
        fail_if_nonzero=False,
    )


def annotate_build_state(org, pipeline, build_info, skip_tasks_csv=""):
    number = build_info.get("number")
    web_url = build_info.get("web_url")
    state = build_info.get("state", "unknown")
    context = f"testing-presubmit-{pipeline}"
    skip_suffix = f" (skipping `{skip_tasks_csv}`)" if skip_tasks_csv else " (skipping none)"
    if not is_build_finished(build_info):
        annotate(
            context,
            "info",
            f"Running `{org}/{pipeline}`: [build #{number}]({web_url}){skip_suffix}",
        )
    elif state == "passed":
        annotate(
            context,
            "success",
            f"Passed `{org}/{pipeline}`: [build #{number}]({web_url}) (`{state}`){skip_suffix}",
        )
    else:
        annotate(
            context,
            "error",
            f"Failed `{org}/{pipeline}`: [build #{number}]({web_url}) (`{state}`){skip_suffix}",
        )


def upload_rollback_step(org):
    annotate(
        f"presubmits-rollback-{org}",
        "error",
        "First check whether the failure is infra (e.g. the `:pipeline:` step failed) "
        "vs. real test failures on the new VM image, then choose whether to roll back or continue "
        "in the unblock step.",
    )
    if not shutil.which("buildkite-agent"):
        return 1
    if org == "bazel":
        families = os.environ.get("BAZEL_VM_NAMES", "")
        groups = os.environ.get("BAZEL_PROD_INSTANCE_GROUPS", "")
    else:
        families = groups = os.environ.get("BAZEL_TEST_VM_NAMES", "")
    bazelci.execute_command(
        ["buildkite-agent", "pipeline", "upload", "../pipelines/vm-image-rollback.yml"],
        env={**os.environ, "ROLLBACK_FAMILIES": families, "ROLLBACK_GROUPS": groups},
    )
    return 0


def parse_pipelines(raw_args):
    return [slug.strip() for arg in raw_args for slug in arg.split(",") if slug.strip()]


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    pipelines = parse_pipelines(argv)
    if not pipelines:
        bazelci.eprint("Usage: trigger_testing_presubmits.py <pipeline> [<pipeline> ...]")
        return 1

    test_vm_names = os.environ.get("BAZEL_TEST_VM_NAMES", "")
    skip_tasks = select_skip_tasks(test_vm_names)
    skip_tasks_csv = ",".join(skip_tasks)
    if skip_tasks_csv:
        print(
            f"Skipping tasks for BAZEL_TEST_VM_NAMES={test_vm_names!r}: {skip_tasks_csv}",
            flush=True,
        )
    else:
        print("Skipping tasks: none", flush=True)

    build_url = os.environ.get("BUILDKITE_BUILD_URL", "")
    message = f"VM image validation for {build_url}" if build_url else "VM image validation"
    if skip_tasks_csv:
        message = f"{message} (skip: {skip_tasks_csv})"

    trigger_env = {"DISABLE_BAZEL_DIFF": "1"}
    if skip_tasks_csv:
        trigger_env[bazelci.SKIP_TASKS_ENV_VAR] = skip_tasks_csv

    tracked = []
    try:
        for pipeline in pipelines:
            client = bazelci.BuildkiteClient(org=ORG, pipeline=pipeline)
            build_info = client.trigger_new_build("HEAD", message=message, env=trigger_env)
            number = build_info["number"]
            web_url = build_info["web_url"]
            state = build_info.get("state", "unknown")
            print(
                f"Triggered {ORG}/{pipeline} build #{number}: {web_url} (state={state})",
                flush=True,
            )
            annotate_build_state(ORG, pipeline, build_info, skip_tasks_csv)
            tracked.append(
                {
                    "pipeline": pipeline,
                    "client": client,
                    "number": number,
                    "build_info": build_info,
                }
            )

        while not all(is_build_finished(entry["build_info"]) for entry in tracked):
            time.sleep(POLL_INTERVAL_SECONDS)
            for entry in tracked:
                if not is_build_finished(entry["build_info"]):
                    entry["build_info"] = entry["client"].get_build_info(entry["number"])
                    if is_build_finished(entry["build_info"]):
                        annotate_build_state(
                            ORG, entry["pipeline"], entry["build_info"], skip_tasks_csv
                        )

            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            states_summary = ", ".join(
                f"{e['pipeline']}#{e['number']}={e['build_info'].get('state', 'unknown')}"
                for e in tracked
            )
            print(f"[{timestamp}] {states_summary}", flush=True)
    except (bazelci.BuildkiteException, subprocess.CalledProcessError, requests.RequestException) as ex:
        bazelci.eprint(ex)
        annotate(
            "testing-presubmits-error",
            "error",
            f"Failed while running testing presubmits: `{ex}`",
        )
        return 1

    print("\nFinal presubmit results:", flush=True)
    for entry in tracked:
        state = entry["build_info"].get("state", "unknown")
        web_url = entry["build_info"].get("web_url")
        print(
            f"  {ORG}/{entry['pipeline']} build #{entry['number']}: {state} ({web_url})",
            flush=True,
        )

    if all(e["build_info"].get("state") == "passed" for e in tracked):
        return 0
    return upload_rollback_step(ORG)


if __name__ == "__main__":
    sys.exit(main())
