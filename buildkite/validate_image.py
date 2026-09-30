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

import argparse
import json
import os
import re
import sys
import time
from typing import Dict, List, Optional, Tuple

import bazelci

PRESUBMIT_PIPELINES = ["bazel-bazel-github-presubmit", "google-bazel-presubmit"]
POSTSUBMIT_PIPELINE = "bazel-bazel"

SOURCE_ORG = "bazel"
TESTING_ORG = "bazel-testing"
PROD_ORG = "bazel"

FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
ACTIVE_STATES = frozenset(["creating", "scheduled", "running", "canceling"])
PASSED_STATE = "passed"


def get_token(org: str) -> str:
    env_token = os.environ.get("BUILDKITE_API_TOKEN", "").strip()
    if env_token:
        return env_token
    project = bazelci.CLOUD_PROJECTS_PER_ORG.get(org, "bazel-public")
    for secret in (
        f"{org}-image-validation-buildkite-token",
        f"{org}-bazelcipy-BuildkiteClient-token",
    ):
        try:
            cmd = [
                bazelci.gcloud_command(),
                "secrets",
                "versions",
                "access",
                "latest",
                f"--secret={secret}",
                f"--project={project}",
            ]
            return bazelci.execute_command_and_get_output(
                cmd, print_output=False
            ).strip()
        except Exception:
            continue
    raise bazelci.BuildkiteException(
        f"Could not retrieve Buildkite API token for org '{org}'."
    )


def get_green_master_commit(client: bazelci.BuildkiteClient, pipeline: str) -> str:
    query = [
        ("branch", "master"),
        ("state", "passed"),
        ("page", "1"),
        ("per_page", "5"),
    ]
    for build in client.get_build_info_list(query):
        commit = build.get("commit")
        if commit and FULL_SHA_RE.match(commit):
            return commit
    # Fallback without branch filter in case pipeline doesn't tag master branch explicitly
    for build in client.get_build_info_list(
        [("state", "passed"), ("page", "1"), ("per_page", "5")]
    ):
        commit = build.get("commit")
        if commit and FULL_SHA_RE.match(commit):
            return commit
    raise bazelci.BuildkiteException(
        f"No passed master build found for pipeline '{pipeline}'."
    )


def save_commits(commits: Dict[str, str]) -> None:
    if os.environ.get("BUILDKITE_BUILD_ID"):
        bazelci.execute_command(
            [
                "buildkite-agent",
                "meta-data",
                "set",
                "validation_commits",
                json.dumps(commits),
            ],
            fail_if_nonzero=False,
        )


def load_commits() -> Dict[str, str]:
    if not os.environ.get("BUILDKITE_BUILD_ID"):
        return {}
    try:
        raw = bazelci.execute_command_and_get_output(
            ["buildkite-agent", "meta-data", "get", "validation_commits"],
            print_output=False,
        ).strip()
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


def wait_for_builds(
    runs: List[Tuple[str, bazelci.BuildkiteClient, Dict]],
    timeout_seconds: int = 7200,
    poll_interval_seconds: int = 30,
) -> Tuple[bool, Dict[int, Dict]]:
    deadline = time.monotonic() + timeout_seconds
    pending = {build["number"]: (pipeline, client) for pipeline, client, build in runs}
    latest_info: Dict[int, Dict] = {}
    while pending:
        still_pending = {}
        for num, (pipeline, client) in pending.items():
            info = client.get_build_info(num)
            latest_info[num] = info
            state = info.get("state")
            if state in ACTIVE_STATES:
                still_pending[num] = (pipeline, client)
            else:
                bazelci.eprint(
                    f"[{pipeline}] Build #{num} finished with state '{state}'."
                )
        pending = still_pending
        if not pending:
            break
        if time.monotonic() >= deadline:
            bazelci.eprint("Timed out waiting for validation builds.")
            return False, latest_info
        time.sleep(poll_interval_seconds)

    all_passed = True
    for pipeline, _, build in runs:
        info = latest_info.get(build["number"], {})
        state = info.get("state")
        if state != PASSED_STATE:
            bazelci.eprint(
                f"[{pipeline}] Build #{build['number']} failed with state '{state}': {info.get('web_url')}"
            )
            all_passed = False
    return all_passed, latest_info


def annotate_summary(
    stage: str,
    runs: List[Tuple[str, bazelci.BuildkiteClient, Dict]],
    latest_info: Dict[int, Dict],
    passed: bool,
) -> None:
    if not os.environ.get("BUILDKITE_BUILD_ID"):
        return
    style = "success" if passed else "error"
    items = []
    for pipeline, _, build in runs:
        info = latest_info.get(build["number"], {})
        items.append(
            f"* **{pipeline}**: [#{build['number']}]({info.get('web_url', '')}) - `{info.get('state', 'unknown')}`"
        )
    body = f"### VM Image Validation ({stage.capitalize()})\n\n" + "\n".join(items)
    bazelci.execute_command(
        [
            "buildkite-agent",
            "annotate",
            f"--style={style}",
            f"--context=validate-image-{stage}",
            body,
        ],
        fail_if_nonzero=False,
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate VM image in testing or prod."
    )
    parser.add_argument("--stage", choices=["testing", "prod"], default="testing")
    parser.add_argument("--timeout", type=int, default=7200)
    parser.add_argument("--poll_interval", type=int, default=30)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    try:
        runs: List[Tuple[str, bazelci.BuildkiteClient, Dict]] = []
        if args.stage == "testing":
            # 1. Get green commit from master in presubmit pipelines in bazel org
            src_token = get_token(SOURCE_ORG)
            tgt_token = (
                get_token(TESTING_ORG) if TESTING_ORG != SOURCE_ORG else src_token
            )
            commits = {}
            for p in PRESUBMIT_PIPELINES:
                src_client = bazelci.BuildkiteClient(
                    org=SOURCE_ORG, pipeline=p, token=src_token
                )
                commits[p] = get_green_master_commit(src_client, p)
                bazelci.eprint(f"[{p}] Using green master commit: {commits[p][:8]}")

            save_commits(commits)

            # 2. Rerun them in the testing org
            for p, commit in commits.items():
                tgt_client = bazelci.BuildkiteClient(
                    org=TESTING_ORG, pipeline=p, token=tgt_token
                )
                build = tgt_client.trigger_new_build(
                    commit=commit,
                    branch="master",
                    message=f"Validate VM image (testing) at {commit[:8]}",
                )
                bazelci.eprint(
                    f"[{p}] Triggered build #{build['number']} in {TESTING_ORG}: {build.get('web_url')}"
                )
                runs.append((p, tgt_client, build))

        else:  # prod
            # 1. Retrieve the two commits from metadata (or query bazel org as fallback)
            saved = load_commits()
            token = get_token(PROD_ORG)
            commits = {}
            for p in PRESUBMIT_PIPELINES:
                if p in saved:
                    commits[p] = saved[p]
                else:
                    src_client = bazelci.BuildkiteClient(
                        org=SOURCE_ORG, pipeline=p, token=token
                    )
                    commits[p] = get_green_master_commit(src_client, p)
                bazelci.eprint(f"[{p}] Using commit: {commits[p][:8]}")

            # 2. Rerun those two commits in prod again
            for p, commit in commits.items():
                client = bazelci.BuildkiteClient(org=PROD_ORG, pipeline=p, token=token)
                build = client.trigger_new_build(
                    commit=commit,
                    branch="master",
                    message=f"Validate VM image (prod) at {commit[:8]}",
                )
                bazelci.eprint(
                    f"[{p}] Triggered build #{build['number']} in {PROD_ORG}: {build.get('web_url')}"
                )
                runs.append((p, client, build))

            # 3. With the post submit too
            post_client = bazelci.BuildkiteClient(
                org=SOURCE_ORG, pipeline=POSTSUBMIT_PIPELINE, token=token
            )
            post_commit = get_green_master_commit(post_client, POSTSUBMIT_PIPELINE)
            bazelci.eprint(
                f"[{POSTSUBMIT_PIPELINE}] Using green master commit: {post_commit[:8]}"
            )
            post_build = post_client.trigger_new_build(
                commit=post_commit,
                branch="master",
                message=f"Validate VM image (prod postsubmit) at {post_commit[:8]}",
            )
            bazelci.eprint(
                f"[{POSTSUBMIT_PIPELINE}] Triggered build #{post_build['number']} in {PROD_ORG}: {post_build.get('web_url')}"
            )
            runs.append((POSTSUBMIT_PIPELINE, post_client, post_build))

        passed, latest_info = wait_for_builds(runs, args.timeout, args.poll_interval)
        annotate_summary(args.stage, runs, latest_info, passed)
        return 0 if passed else 1

    except bazelci.BuildkiteException as ex:
        bazelci.eprint(f"Error: {ex}")
        return ex.exit_code


if __name__ == "__main__":
    sys.exit(main())
