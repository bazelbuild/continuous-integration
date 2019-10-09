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
import os
import sys
import threading

import bazelci

INCOMPATIBLE_FLAGS = bazelci.fetch_incompatible_flags()

BUILDKITE_ORG = os.environ["BUILDKITE_ORGANIZATION_SLUG"]

PIPELINE = os.environ["BUILDKITE_PIPELINE_SLUG"]


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


def print_flags_ready_to_flip(failed_jobs_per_flag):
    info_text = ["#### The following flags didn't break any passing jobs"]
    for flag in sorted(list(INCOMPATIBLE_FLAGS.keys())):
        if flag not in failed_jobs_per_flag:
            github_url = INCOMPATIBLE_FLAGS[flag]
            info_text.append(f"* **{flag}** " + get_html_link_text(":github:", github_url))
    if len(info_text) == 1:
        return
    print_info("flags_ready_to_flip", "success", info_text)


def print_already_fail_jobs(already_failing_jobs):
    info_text = ["#### The following jobs already fail without incompatible flags"]
    info_text += merge_and_format_jobs(already_failing_jobs, "* **{}**: {}")
    if len(info_text) == 1:
        return
    print_info("already_fail_jobs", "warning", info_text)


def print_projects_need_to_migrate(failed_jobs_per_flag):
    info_text = ["#### The following projects need migration"]
    jobs_need_migration = {}
    for jobs in failed_jobs_per_flag.values():
        for job in jobs.values():
            jobs_need_migration[job["name"]] = job

    job_list = jobs_need_migration.values()
    job_num = len(job_list)
    if job_num == 0:
        return

    projects = set()
    for job in job_list:
        project, _ = get_pipeline_and_platform(job)
        projects.add(project)
    project_num = len(projects)

    s1 = "" if project_num == 1 else "s"
    s2 = "s" if project_num == 1 else ""
    info_text.append(
        f"<details><summary>{project_num} project{s1} need{s2} migration, click to see details</summary><ul>"
    )

    entries = merge_and_format_jobs(job_list, "    <li><strong>{}</strong>: {}</li>")
    info_text += entries
    info_text.append("</ul></details>")

    info_str = "\n".join(info_text)
    bazelci.execute_command(
        [
            "buildkite-agent",
            "annotate",
            "--append",
            f"--context=projects_need_migration",
            f"--style=error",
            f"\n{info_str}\n",
        ]
    )


def print_flags_need_to_migrate(failed_jobs_per_flag):
    # The info box printed later is above info box printed before,
    # so reverse the flag list to maintain the same order.
    for flag in sorted(list(failed_jobs_per_flag.keys()), reverse=True):
        jobs = failed_jobs_per_flag[flag]
        if jobs:
            github_url = INCOMPATIBLE_FLAGS[flag]
            info_text = []
            info_text.append(f"* **{flag}** " + get_html_link_text(":github:", github_url))
            info_text += merge_and_format_jobs(jobs.values(), "  - **{}**: {}")
            # Use flag as the context so that each flag gets a different info box.
            print_info(flag, "error", info_text)
    if len(info_text) == 1:
        return
    info_text = ["#### Downstream projects need to migrate for the following flags:"]
    print_info("flags_need_to_migrate", "error", info_text)


def merge_and_format_jobs(jobs, line_pattern):
    # Merges all jobs for a single pipeline into one line.
    # Example:
    #   pipeline (platform1)
    #   pipeline (platform2)
    #   pipeline (platform3)
    # with line_pattern ">> {}: {}" becomes
    #   >> pipeline: platform1, platform2, platform3
    jobs = list(jobs)
    jobs.sort(key=lambda s: s["name"].lower())
    jobs_per_pipeline = collections.defaultdict(list)
    for job in jobs:
        pipeline, platform = get_pipeline_and_platform(job)
        jobs_per_pipeline[pipeline].append(get_html_link_text(platform, job["web_url"]))

    return [
        line_pattern.format(pipeline, ", ".join(platforms))
        for pipeline, platforms in jobs_per_pipeline.items()
    ]


def get_pipeline_and_platform(job):
    name, _, platform = job["name"].rpartition("(")
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

    print_flags_need_to_migrate(failed_jobs_per_flag)

    print_projects_need_to_migrate(failed_jobs_per_flag)

    print_already_fail_jobs(already_failing_jobs)

    print_flags_ready_to_flip(failed_jobs_per_flag)


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
