#!/usr/bin/env python3
#
# Copyright 2018 The Bazel Authors. All rights reserved.
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
import base64
import json
import os
import re
import subprocess
import sys
import yaml

import bazelci
from bazelci import BuildkiteException

BUILD_STATUS_API_URL = "https://api.buildkite.com/v2/organizations/bazel/pipelines/bazel-at-release-plus-incompatible-flags/builds/"

ENCRYPTED_BUILDKITE_API_TOKEN = """
CiQA4DEB9ldzC+E39KomywtqXfaQ86hhulgeDsicds2BuvbCYzsSUAAqwcvXZPh9IMWlwWh94J2F
exosKKaWB0tSRJiPKnv2NPDfEqGul0ZwVjtWeASpugwxxKeLhFhPMcgHMPfndH6j2GEIY6nkKRbP
uwoRMCwe
""".strip()


def buildkite_token():
    return (
        subprocess.check_output(
            [
                bazelci.gcloud_command(),
                "kms",
                "decrypt",
                "--project",
                "bazel-untrusted",
                "--location",
                "global",
                "--keyring",
                "buildkite",
                "--key",
                "buildkite-untrusted-api-token",
                "--ciphertext-file",
                "-",
                "--plaintext-file",
                "-",
            ],
            input=base64.b64decode(ENCRYPTED_BUILDKITE_API_TOKEN),
            env=os.environ,
        )
        .decode("utf-8")
        .strip()
    )


def get_build_status_api_url(build_number):
    return BUILD_STATUS_API_URL + "%s?access_token=%s" % (build_number, buildkite_token())


def get_build_info(build_number):
    output = subprocess.check_output(["curl", get_build_status_api_url(build_number)]).decode(
        "utf-8"
    )
    build_info = json.loads(output)
    return build_info


def get_failing_jobs(build_info):
    failing_jobs = []
    for job in build_info["jobs"]:
        if "state" in job and job["state"] == "failed":
            command = job["command"]
            # Skip if the job command doesn't contain --incompatible_flag
            if command.find("--incompatible_flag") == -1:
                continue

            # Get rid of the incompatible flags in the command line because we are going to test them individually
            command_without_incompatible_flags = " ".join(
                [i for i in command.split(" ") if not i.startswith("--incompatible_flag")]
            )

            # Recover a map for agent query rules
            agents = {}
            for rule in job["agent_query_rules"]:
                key, value = rule.split("=")
                agents[key] = value

            failing_jobs.append(
                {
                    "name": job["name"],
                    "command": command_without_incompatible_flags.split("\n"),
                    "agents": agents,
                }
            )
    return failing_jobs


def print_steps_for_failing_jobs(build_number):
    build_info = get_build_info(build_number)
    failing_jobs = get_failing_jobs(build_info)
    incompatible_flags = list(bazelci.fetch_incompatible_flags().keys())
    pipeline_steps = []
    for incompatible_flag in incompatible_flags:
        for job in failing_jobs:
            command = list(job["command"])
            command[1] = command[1] + " --incompatible_flag=" + incompatible_flag
            pipeline_steps.append(
                {
                    "label": "%s: %s" % (incompatible_flag, job["name"]),
                    "command": command,
                    "agents": job["agents"].copy(),
                }
            )
    print(yaml.dump({"steps": pipeline_steps}))


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Script for testing failing jobs with individual incompatible flag"
    )
    parser.add_argument("--build_number", type=str)

    args = parser.parse_args(argv)
    try:
        if args.build_number:
            print_steps_for_failing_jobs(args.build_number)
        else:
            parser.print_help()
            return 2

    except BuildkiteException as e:
        bazelci.eprint(str(e))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
