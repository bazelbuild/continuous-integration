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
import sys
import yaml

import bazelci
from bazelci import BuildkiteException

# Buildkite has a max jobs limit at 2000, but that includes jobs already
# executed by the pipeline. Setting arbitrary lower number to make sure we fit
# under.
BUILDKITE_MAX_JOBS_LIMIT = 1500

BUILDKITE_ORG = "bazel"

PIPELINE = "bazel-at-release-plus-incompatible-flags"


def get_failing_jobs(build_info):
    failing_jobs = []
    for job in build_info["jobs"]:
        if "state" in job and job["state"] == "failed":
            command = job["command"]
            if not command:
                bazelci.eprint("'command' field not found in the job: " + str(job))
                continue
            # Skip if the job is not a runner job
            if command.find("bazelci.py runner") == -1:
                continue

            # Get rid of the incompatible flags in the command line because we are going to test them individually
            command_without_incompatible_flags = " ".join(
                [i for i in command.split(" ") if not i.startswith("--incompatible_flag")]
            )

            # Recover the task name from job command
            flags = get_flags_from_command(command)
            task = flags.get("task")
            if not task:
                raise BuildkiteException(
                    "The following command has no --task argument: %s." % command
                )

            # Fetch the original job config to retrieve the platform name.
            job_config = bazelci.load_config(
                http_url=flags.get("http_config"), file_config=flags.get("file_config")
            )

            # The config can either contain a "tasks" dict (new format) or a "platforms" dict (legacy format).
            all_tasks = job_config.get("tasks", job_config.get("platforms"))
            if not all_tasks:
                raise BuildkiteException(
                    "Malformed configuration: No 'tasks' or 'platforms' entry found."
                )

            task_config = all_tasks.get(task)
            if not task_config:
                raise BuildkiteException(
                    "Configuration does not contain an entry for task '%s'" % task
                )

            # Shortcut: Users can skip the "platform" field if its value equals the task name.
            platform = task_config.get("platform") or task
            failing_jobs.append(
                {
                    "name": job["name"],
                    "command": command_without_incompatible_flags.split("\n"),
                    "platform": platform,
                }
            )
    return failing_jobs


def get_flags_from_command(command):
    flags = {}
    for entry in command.split(" "):
        if entry.startswith("--") and "=" in entry:
            key, _, value = entry[2:].partition("=")
            flags[key] = value

    return flags


def print_steps_for_failing_jobs(build_info):
    failing_jobs = get_failing_jobs(build_info)
    incompatible_flags = list(bazelci.fetch_incompatible_flags().keys())
    pipeline_steps = []
    counter = 0
    for incompatible_flag in incompatible_flags:
        for job in failing_jobs:
            counter += 1
            if counter > BUILDKITE_MAX_JOBS_LIMIT:
                continue
            label = "%s: %s" % (incompatible_flag, job["name"])
            command = list(job["command"])
            command[1] = command[1] + " --incompatible_flag=" + incompatible_flag
            pipeline_steps.append(bazelci.create_step(label, command, job["platform"]))
    if counter > BUILDKITE_MAX_JOBS_LIMIT:
        bazelci.eprint(
            "We only allow "
            + str(BUILDKITE_MAX_JOBS_LIMIT)
            + " jobs to be registered at once, skipping "
            + str(counter - BUILDKITE_MAX_JOBS_LIMIT)
            + " jobs."
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
            client = bazelci.BuildkiteClient(org=BUILDKITE_ORG, pipeline=PIPELINE)
            build_info = client.get_build_info(args.build_number)
            print_steps_for_failing_jobs(build_info)
        else:
            parser.print_help()
            return 2

    except BuildkiteException as e:
        bazelci.eprint(str(e))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
