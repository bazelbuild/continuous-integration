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
import collections
import sys
import threading

import bazelci

INCOMPATIBLE_FLAGS = bazelci.fetch_incompatible_flags()

BUILDKITE_ORG = "bazel"

PIPELINE = "bazelisk-plus-incompatible-flags"


class LogFetcher(threading.Thread):
    def __init__(self, job, client):
        threading.Thread.__init__(self)
        self.job = job
        self.client = client
        self.log = None

    def run(self):
        self.log = self.client.get_build_log(self.job)


def process_build_log(failed_jobs_per_flag, already_failing_jobs, log, job):
    if "Failure: Command failed, even without incompatible flags." in log:
        already_failing_jobs.append(job)

    # bazelisk --migrate might run for multiple times for run / build / test,
    # so there could be several "+++ Result" sections.
    while "+++ Result" in log:
        index_success = log.rfind("Command was successful with the following flags:")
        index_failure = log.rfind("Migration is needed for the following flags:")
        if index_success == -1 or index_failure == -1:
            raise bazelci.BuildkiteException("Cannot recognize log of " + job["web_url"])
        lines = log[index_failure:].split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("--incompatible_") and line in INCOMPATIBLE_FLAGS:
                failed_jobs_per_flag[line][job["id"]] = job
        log = log[0 : log.rfind("+++ Result")]

    # If the job failed for other reasons, we add it into already failing jobs.
    if job["state"] == "failed":
        already_failing_jobs.append(job)


def get_html_link_text(content, link):
    return f'<a href="{link}" target="_blank">{content}</a>'


def construct_success_info(failed_jobs_per_flag):
    info_text = ["#### The following flags didn't break any passing jobs"]
    for flag in INCOMPATIBLE_FLAGS:
        if flag not in failed_jobs_per_flag:
            github_url = INCOMPATIBLE_FLAGS[flag]
            info_text.append(f"* **{flag}** " + get_html_link_text(":github:", github_url))
    if len(info_text) == 1:
        return None
    return info_text


def construct_warning_info(already_failing_jobs):
    info_text = ["#### The following jobs already fail without incompatible flags"]
    info_text += merge_and_format_jobs(already_failing_jobs, "* ")
    if len(info_text) == 1:
        return None
    return info_text


def construct_failure_info(failed_jobs_per_flag):
    info_text = ["#### Downstream projects need to migrate for the following flags"]
    for flag, jobs in failed_jobs_per_flag.items():
        if jobs:
            github_url = INCOMPATIBLE_FLAGS[flag]
            info_text.append(f"* **{flag}** " + get_html_link_text(":github:", github_url))
            info_text += merge_and_format_jobs(jobs.values(), "  - ")
    if len(info_text) == 1:
        return None
    return info_text


def merge_and_format_jobs(jobs, line_prefix):
    # Merges all jobs for a single pipeline into one line.
    # Example:
    #   pipeline (platform1)
    #   pipeline (platform2)
    #   pipeline (platform3)
    # with line_prefix ">> " becomes
    #   >> pipeline: platform1, platform2, platform3
    jobs_per_pipeline = collections.defaultdict(list)
    for job in jobs:
        pipeline, platform = get_pipeline_and_platform(job)
        jobs_per_pipeline[pipeline].append(get_html_link_text(platform, job["web_url"]))

    return ["{}**{}**: {}".format(line_prefix, pipeline, ", ".join(platforms)) for pipeline, platforms in jobs_per_pipeline.items()]


def get_pipeline_and_platform(job):
    name, _, platform = job["name"].partition('(')
    end = platform.rfind(")")
    return name.strip(), platform[:end].strip()


def print_info(context, style, info):
    # CHUNK_SIZE is to prevent buildkite-agent "argument list too long" error
    CHUNK_SIZE = 20
    for i in range(0, len(info), CHUNK_SIZE):
        info_str = "\n".join(info[i : i + CHUNK_SIZE])
        bazelci.execute_command(
            [
                "buildkite-agent",
                "annotate",
                "--append",
                f"--context={context}",
                f"--style={style}",
                f"\n{info_str}\n",
            ]
        )


def print_result_info(build_number, client):
    build_info = client.get_build_info(build_number)

    already_failing_jobs = []

    # dict(flag name -> dict(job id -> job))
    failed_jobs_per_flag = collections.defaultdict(dict)

    threads = []
    for job in build_info["jobs"]:
        # Some irrelevant job has no "state" field
        if "state" in job:
            thread = LogFetcher(job, client)
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()
        process_build_log(failed_jobs_per_flag, already_failing_jobs, thread.log, thread.job)

    failure_info = construct_failure_info(failed_jobs_per_flag)

    warning_info = construct_warning_info(already_failing_jobs)

    success_info = construct_success_info(failed_jobs_per_flag)

    if failure_info:
        print_info("failure", "error", failure_info)

    if warning_info:
        print_info("warning", "warning", warning_info)

    if success_info:
        print_info("success", "success", success_info)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Script to aggregate `bazelisk --migrate` test result for incompatible flags and generate pretty Buildkite info messages."
    )
    parser.add_argument("--build_number", type=str)

    args = parser.parse_args(argv)
    try:
        if args.build_number:
            client = bazelci.BuildkiteClient(org=BUILDKITE_ORG, pipeline=PIPELINE)
            print_result_info(args.build_number, client)
        else:
            parser.print_help()
            return 2

    except bazelci.BuildkiteException as e:
        bazelci.eprint(str(e))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
