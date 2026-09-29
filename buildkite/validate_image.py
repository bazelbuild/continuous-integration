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
import dataclasses
import os
import re
import sys
import time
from typing import Dict, List, Optional, Set, Tuple

import bazelci

DEFAULT_ORG = "bazel-testing"
DEFAULT_PIPELINES = ("Bazel :bazel:", "Bazel :bazel: Github Presubmit", "Google Bazel Presubmit")
DEFAULT_SECRET_PROJECT = "bazel-public"
DEFAULT_TIMEOUT_SECONDS = 7200
DEFAULT_POLL_INTERVAL_SECONDS = 30

FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
ACTIVE_BUILD_STATES = frozenset(["creating", "scheduled", "running", "canceling"])
ACTIVE_JOB_STATES = frozenset(
    ["creating", "waiting", "waiting_failed", "blocked", "unblocked", "limiting", "limited"]
    + ["scheduled", "assigned", "accepted", "running", "canceling"]
)
FAILED_JOB_STATES = frozenset(["failed", "timed_out", "expired"])


@dataclasses.dataclass
class PipelineValidationRun:
    name: str
    slug: str
    client: bazelci.BuildkiteClient
    baseline_build: Dict
    validation_build: Dict
    retried_jobs: Set[str] = dataclasses.field(default_factory=set)
    done: bool = False
    timed_out: bool = False


def to_pipeline_slug(name_or_slug: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name_or_slug.lower()).strip("-")


def parse_pipeline_list(raw_pipelines: Optional[List[str]]) -> List[str]:
    if not raw_pipelines:
        env_val = os.environ.get("BAZEL_VALIDATE_PIPELINES", "").strip()
        raw_pipelines = [env_val] if env_val else list(DEFAULT_PIPELINES)
    items = raw_pipelines[0].split(",") if len(raw_pipelines) == 1 else raw_pipelines
    return [p.strip() for p in items if p.strip()]


def get_buildkite_token(
    org: str, secret_name: Optional[str] = None, secret_project: str = DEFAULT_SECRET_PROJECT
) -> str:
    env_token = os.environ.get("BUILDKITE_API_TOKEN", "").strip()
    if env_token:
        return env_token
    secret = secret_name or f"{org}-image-validation-buildkite-token"
    cmd = [bazelci.gcloud_command(), "secrets", "versions", "access", "latest"]
    cmd += [f"--secret={secret}", f"--project={secret_project}"]
    return bazelci.execute_command_and_get_output(cmd, print_output=False).strip()


def is_full_commit_sha(commit: Optional[str]) -> bool:
    return bool(commit and FULL_SHA_RE.match(commit))


def find_baseline_build(client: bazelci.BuildkiteClient, slug: str) -> Dict:
    query = [("state", "passed"), ("page", "1"), ("per_page", "10")]
    if "presubmit" not in slug:
        builds = [
            b for b in client.get_build_info_list([("branch", "master"), *query])
            if is_full_commit_sha(b.get("commit"))
        ]
        if builds:
            return builds[0]
    builds = [b for b in client.get_build_info_list(query) if is_full_commit_sha(b.get("commit"))]
    if not builds:
        raise bazelci.BuildkiteException(f"No passed baseline build found for pipeline '{slug}'.")
    return builds[0]


def trigger_validation_build(client: bazelci.BuildkiteClient, baseline: Dict) -> Dict:
    return client.trigger_new_build(
        commit=baseline["commit"],
        message=f"Validate VM image (baseline build #{baseline['number']})",
        env=dict(baseline.get("env") or {}),
        branch=baseline.get("branch") or "master",
    )


def extract_jobs(build: Dict) -> Dict[str, Dict]:
    return {
        (j.get("name") or j.get("label") or j.get("command") or j.get("id")): j
        for j in build.get("jobs", [])
        if j.get("type") in (None, "script") and j.get("state")
    }


def is_job_passed(job: Dict) -> bool:
    return job.get("state") == "passed" or bool(job.get("soft_failed"))


def is_job_failed(job: Dict) -> bool:
    return job.get("state") in FAILED_JOB_STATES and not bool(job.get("soft_failed"))


def poll_and_retry_builds(
    runs: List[PipelineValidationRun], timeout_seconds: int, poll_interval_seconds: int
) -> None:
    deadline = time.monotonic() + timeout_seconds
    while not all(r.done for r in runs):
        for r in runs:
            if r.done:
                continue
            r.validation_build = r.client.get_build_info(r.validation_build["number"])
            jobs = extract_jobs(r.validation_build)
            retried_now = False
            for key, job in jobs.items():
                if is_job_failed(job) and key not in r.retried_jobs:
                    bazelci.eprint(f"[{r.slug}] Retrying failed job '{key}' ({job.get('web_url')})...")
                    r.client.trigger_job_retry(r.validation_build["number"], job["id"])
                    r.retried_jobs.add(key)
                    retried_now = True

            build_active = r.validation_build.get("state") in ACTIVE_BUILD_STATES
            jobs_active = any(j.get("state") in ACTIVE_JOB_STATES for j in jobs.values())
            if not retried_now and not build_active and not jobs_active:
                r.done = True
                bazelci.eprint(
                    f"[{r.slug}] Build #{r.validation_build['number']} finished "
                    f"with state '{r.validation_build.get('state')}'."
                )

        if all(r.done for r in runs):
            break
        if time.monotonic() >= deadline:
            for r in runs:
                if not r.done:
                    r.timed_out = True
                    bazelci.eprint(f"[{r.slug}] Timed out waiting for build #{r.validation_build['number']}.")
            break
        time.sleep(poll_interval_seconds)


def get_log_tail(client: bazelci.BuildkiteClient, job: Dict, max_lines: int = 10) -> str:
    if not job.get("raw_log_url"):
        return ""
    try:
        lines = [ln.rstrip() for ln in client.get_build_log(job).splitlines() if ln.strip()]
        return "\n".join(lines[-max_lines:])
    except Exception:
        return ""


def evaluate_run(
    run: PipelineValidationRun,
) -> Tuple[List[str], List[Dict], List[Tuple[str, str, Dict, str]], bool]:
    base_jobs, val_jobs = extract_jobs(run.baseline_build), extract_jobs(run.validation_build)
    passed_keys, flaky_jobs, new_failures = [], [], []
    for key, val_job in val_jobs.items():
        base_job = base_jobs.get(key)
        base_state = base_job.get("state", "missing") if base_job else "missing"
        if is_job_passed(val_job):
            (flaky_jobs if key in run.retried_jobs else passed_keys).append(
                val_job if key in run.retried_jobs else key
            )
        elif not base_job or is_job_passed(base_job):
            new_failures.append((key, base_state, val_job, get_log_tail(run.client, val_job)))

    has_regression = (
        bool(new_failures) or run.timed_out or (run.validation_build.get("state") != "passed")
    )
    return passed_keys, flaky_jobs, new_failures, has_regression


def format_and_evaluate(org: str, runs: List[PipelineValidationRun]) -> Tuple[str, str, bool]:
    lines = [
        f"#### VM Image Validation (`{org}`)",
        "",
        "| Pipeline | Baseline | Validation | Passed | Flaky (retried) | New Failures | Status |",
        "|---|---|---|---|---|---|---|",
    ]
    regression_details, flaky_details = [], []
    any_regression = any_flaky = False

    for run in runs:
        passed_keys, flaky_jobs, new_failures, has_regression = evaluate_run(run)
        any_regression = any_regression or has_regression
        any_flaky = any_flaky or bool(flaky_jobs)

        b_num, b_url = run.baseline_build["number"], run.baseline_build.get("web_url", "")
        b_sha = (run.baseline_build.get("commit") or "")[:7]
        b_br = run.baseline_build.get("branch") or "master"
        v_num, v_url = run.validation_build["number"], run.validation_build.get("web_url", "")
        v_state = "timed_out" if run.timed_out else (run.validation_build.get("state") or "unknown")
        status = (
            f":x: Failed (`{v_state}`)"
            if has_regression
            else (":warning: Passed (with retries)" if flaky_jobs else ":white_check_mark: Passed")
        )
        lines.append(
            f"| **{run.name}** | [#{b_num}]({b_url}) (`{b_sha}` on `{b_br}`) | [#{v_num}]({v_url}) "
            f"| {len(passed_keys)} | {len(flaky_jobs)} | {len(new_failures)} | {status} |"
        )
        if run.timed_out:
            regression_details.append(f"* **{run.name}**: build [#{v_num}]({v_url}) timed out.")
        elif has_regression and not new_failures:
            regression_details.append(f"* **{run.name}**: build [#{v_num}]({v_url}) ended in `{v_state}`.")

        for key, base_state, val_job, log_tail in new_failures:
            retry_note = " after retry" if key in run.retried_jobs else ""
            regression_details.append(
                f"* **{run.name}**: [{key}]({val_job.get('web_url', v_url)}) "
                f"(baseline: `{base_state}` → validation: `{val_job.get('state', 'failed')}`{retry_note})"
            )
            if log_tail:
                regression_details.append(
                    f"  <details><summary>Log tail</summary>\n\n  ```term\n{log_tail}\n  ```\n  </details>"
                )
        for job in flaky_jobs:
            flaky_details.append(
                f"* **{run.name}**: [{job.get('name') or job.get('id')}]({job.get('web_url', v_url)}) "
                "(failed first attempt, `passed` on retry)"
            )

    if regression_details:
        lines.extend(["", "##### New Failures (Regressions)", *regression_details])
    if flaky_details:
        lines.extend(["", "##### Flaky Jobs (Passed on Retry)", *flaky_details])
    style = "error" if any_regression else ("warning" if any_flaky else "success")
    return "\n".join(lines) + "\n", style, any_regression


def annotate_build(markdown: str, style: str, org: str) -> None:
    print(markdown)
    if os.environ.get("BUILDKITE_BUILD_ID"):
        bazelci.execute_command(
            ["buildkite-agent", "annotate", f"--style={style}", f"--context=validate-image-{org}", markdown],
            fail_if_nonzero=False,
        )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate new VM images against baseline builds.")
    parser.add_argument("--org", default=os.environ.get("BAZEL_VALIDATE_ORG", DEFAULT_ORG))
    parser.add_argument("--pipelines", nargs="*")
    parser.add_argument("--secret", default=os.environ.get("BAZEL_VALIDATE_TOKEN_SECRET"))
    parser.add_argument(
        "--secret_project", default=os.environ.get("BAZEL_VALIDATE_SECRET_PROJECT", DEFAULT_SECRET_PROJECT)
    )
    parser.add_argument(
        "--timeout", type=int, default=int(os.environ.get("BAZEL_VALIDATE_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))
    )
    parser.add_argument(
        "--poll_interval",
        type=int,
        default=int(os.environ.get("BAZEL_VALIDATE_POLL_INTERVAL_SECONDS", str(DEFAULT_POLL_INTERVAL_SECONDS))),
    )
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    try:
        token = get_buildkite_token(args.org, args.secret, args.secret_project)
        runs = []
        for name in parse_pipeline_list(args.pipelines):
            slug = to_pipeline_slug(name)
            client = bazelci.BuildkiteClient(org=args.org, pipeline=slug, token=token)
            baseline = find_baseline_build(client, slug)
            bazelci.eprint(f"[{slug}] Baseline build #{baseline['number']}: {baseline.get('web_url', '')}")
            val_build = trigger_validation_build(client, baseline)
            bazelci.eprint(f"[{slug}] Validation build #{val_build['number']}: {val_build.get('web_url', '')}")
            runs.append(PipelineValidationRun(name, slug, client, baseline, val_build))

        poll_and_retry_builds(runs, args.timeout, args.poll_interval)
        markdown, style, any_regression = format_and_evaluate(args.org, runs)
        annotate_build(markdown, style, args.org)
        return 1 if any_regression else 0
    except bazelci.BuildkiteException as ex:
        bazelci.eprint(f"Validation failed: {ex}")
        return ex.exit_code


if __name__ == "__main__":
    sys.exit(main())
