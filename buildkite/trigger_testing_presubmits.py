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
from datetime import datetime, timezone
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error

import requests

import bazelci

DEFAULT_ORG = "bazel-testing"
DEFAULT_POLL_INTERVAL_SECONDS = 60
DEFAULT_API_RETRIES = 5
TERMINAL_BUILD_STATES = frozenset(["passed", "failed", "canceled", "skipped", "not_run"])
_TOKEN_QUERY_RE = re.compile(r"(access_token=)[^&\s\"']+")
_CLIENT_ERROR_STATUS_RE = re.compile(r": (4\d\d) -")


def redact_tokens(value):
    return _TOKEN_QUERY_RE.sub(r"\1[REDACTED]", str(value))


def is_build_finished(build_info):
    return build_info.get("state") in TERMINAL_BUILD_STATES or bool(build_info.get("finished_at"))


def is_non_retryable_error(ex):
    if isinstance(ex, requests.HTTPError) and ex.response is not None:
        status = ex.response.status_code
        return 400 <= status < 500 and status != 429
    if isinstance(ex, bazelci.BuildkiteException):
        match = _CLIENT_ERROR_STATUS_RE.search(str(ex))
        if match and match.group(1) != "429":
            return True
    return False


def call_with_retries(description, func, retries=DEFAULT_API_RETRIES):
    for attempt in range(retries):
        try:
            return func()
        except (
            bazelci.BuildkiteException,
            requests.RequestException,
            urllib.error.URLError,
            OSError,
            ValueError,
        ) as ex:
            sanitized = redact_tokens(ex)
            if is_non_retryable_error(ex) or attempt == retries - 1:
                raise bazelci.BuildkiteException(f"{description} failed: {sanitized}") from None
            wait_seconds = 2 ** (attempt + 1)
            bazelci.eprint(
                f"{description} failed (attempt {attempt + 1}/{retries}): {sanitized}; "
                f"retrying in {wait_seconds}s..."
            )
            time.sleep(wait_seconds)
    raise bazelci.BuildkiteException(f"{description} failed after {retries} attempts")


def annotation_context(pipeline):
    return f"testing-presubmit-{pipeline}"


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


def annotate_build_state(org, pipeline, build_info):
    number = build_info.get("number")
    web_url = build_info.get("web_url")
    state = build_info.get("state", "unknown")
    context = annotation_context(pipeline)
    if not is_build_finished(build_info):
        annotate(
            context,
            "info",
            f"Running `{org}/{pipeline}`: [build #{number}]({web_url})",
        )
    elif state == "passed":
        annotate(
            context,
            "success",
            f"Passed `{org}/{pipeline}`: [build #{number}]({web_url}) (`{state}`)",
        )
    else:
        annotate(
            context,
            "error",
            f"Failed `{org}/{pipeline}`: [build #{number}]({web_url}) (`{state}`)",
        )


def parse_pipelines(raw_args):
    pipelines = []
    for arg in raw_args:
        for slug in arg.split(","):
            slug = slug.strip()
            if slug:
                pipelines.append(slug)
    return pipelines


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Trigger Bazel presubmit pipelines in bazel-testing and wait for completion."
    )
    parser.add_argument(
        "pipelines",
        nargs="+",
        help="Pipeline slugs to trigger (space- or comma-separated), "
        "e.g. google-bazel-presubmit bazel-bazel-github-presubmit.",
    )
    parser.add_argument(
        "--org",
        default=DEFAULT_ORG,
        help=f"Target Buildkite organization slug (default: {DEFAULT_ORG}).",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help=f"Seconds between build status polls (default: {DEFAULT_POLL_INTERVAL_SECONDS}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned build triggers without calling Secret Manager or Buildkite.",
    )
    args = parser.parse_args(argv)

    pipelines = parse_pipelines(args.pipelines)
    if not pipelines:
        parser.error("At least one pipeline slug must be provided.")

    build_url = os.environ.get("BUILDKITE_BUILD_URL", "")
    message = f"VM image validation for {build_url}" if build_url else "VM image validation"
    trigger_env = {"DISABLE_BAZEL_DIFF": "1"}

    if args.dry_run:
        for pipeline in pipelines:
            print(
                f"[dry-run] Would trigger {args.org}/{pipeline} at HEAD "
                f"with message={message!r}, env={trigger_env}",
                flush=True,
            )
        return 0

    tracked = []
    try:
        for pipeline in pipelines:
            client = bazelci.BuildkiteClient(org=args.org, pipeline=pipeline)
            build_info = call_with_retries(
                f"Triggering {args.org}/{pipeline}",
                lambda c=client: c.trigger_new_build("HEAD", message=message, env=trigger_env),
            )
            number = build_info["number"]
            web_url = build_info["web_url"]
            state = build_info.get("state", "unknown")
            print(
                f"Triggered {args.org}/{pipeline} build #{number}: {web_url} (state={state})",
                flush=True,
            )
            annotate_build_state(args.org, pipeline, build_info)
            tracked.append(
                {
                    "pipeline": pipeline,
                    "client": client,
                    "number": number,
                    "build_info": build_info,
                    "final_annotated": is_build_finished(build_info),
                }
            )

        while not all(is_build_finished(entry["build_info"]) for entry in tracked):
            time.sleep(args.poll_interval)
            for entry in tracked:
                if not is_build_finished(entry["build_info"]):
                    entry["build_info"] = call_with_retries(
                        f"Polling {args.org}/{entry['pipeline']} build #{entry['number']}",
                        lambda e=entry: e["client"].get_build_info(e["number"]),
                    )
                    if is_build_finished(entry["build_info"]) and not entry["final_annotated"]:
                        annotate_build_state(args.org, entry["pipeline"], entry["build_info"])
                        entry["final_annotated"] = True

            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            states_summary = ", ".join(
                f"{e['pipeline']}#{e['number']}={e['build_info'].get('state', 'unknown')}"
                for e in tracked
            )
            print(f"[{timestamp}] {states_summary}", flush=True)

        for entry in tracked:
            if not entry["final_annotated"]:
                annotate_build_state(args.org, entry["pipeline"], entry["build_info"])
                entry["final_annotated"] = True
    except (bazelci.BuildkiteException, subprocess.CalledProcessError) as ex:
        error_msg = redact_tokens(ex)
        bazelci.eprint(error_msg)
        annotate(
            "testing-presubmits-error",
            "error",
            f"Failed while running testing presubmits: `{error_msg}`",
        )
        return 1

    all_passed = True
    print("\nFinal presubmit results:", flush=True)
    for entry in tracked:
        state = entry["build_info"].get("state", "unknown")
        web_url = entry["build_info"].get("web_url")
        print(
            f"  {args.org}/{entry['pipeline']} build #{entry['number']}: {state} ({web_url})",
            flush=True,
        )
        if state != "passed":
            all_passed = False

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
