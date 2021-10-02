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
import re
import subprocess
import sys
import threading

import bazelci

BUILDKITE_ORG = os.environ["BUILDKITE_ORGANIZATION_SLUG"]

PIPELINE = os.environ["BUILDKITE_PIPELINE_SLUG"]

FAIL_IF_MIGRATION_REQUIRED = os.environ.get("USE_BAZELISK_MIGRATE", "").upper() == "FAIL"


INCOMPATIBLE_FLAG_LINE_PATTERN = re.compile(
    r"\s*(?P<flag>--incompatible_\S+)\s*(\(Bazel (?P<version>.+?): (?P<url>.+?)\))?"
)

FlagDetails = collections.namedtuple("FlagDetails", ["bazel_version", "issue_url"])


class LogFetcher(threading.Thread):
    def __init__(self, job, client):
        threading.Thread.__init__(self)
        self.job = job
        self.client = client
        self.log = None

    def run(self):
        self.log = self.client.get_build_log(self.job)


def process_build_log(failed_jobs_per_flag, already_failing_jobs, log, job, details_per_flag):
    if "Failure: Command failed, even without incompatible flags." in log:
        already_failing_jobs.append(job)

    def handle_failing_flags(line, details_per_flag):
        flag = extract_flag_details(line, details_per_flag)
        if flag:
            failed_jobs_per_flag[flag][job["id"]] = job

    # bazelisk --migrate might run for multiple times for run / build / test,
    # so there could be several "+++ Result" sections.
    while "+++ Result" in log:
        index_success = log.rfind("Command was successful with the following flags:")
        index_failure = log.rfind("Migration is needed for the following flags:")
        if index_success == -1 or index_failure == -1:
            raise bazelci.BuildkiteException("Cannot recognize log of " + job["web_url"])

        extract_all_flags(log[index_success:index_failure], extract_flag_details, details_per_flag)
        extract_all_flags(log[index_failure:], handle_failing_flags, details_per_flag)
        log = log[0 : log.rfind("+++ Result")]

    # If the job failed for other reasons, we add it into already failing jobs.
    if job["state"] == "failed":
        already_failing_jobs.append(job)


def extract_all_flags(log, line_callback, details_per_flag):
    for line in log.split("\n"):
        line_callback(line, details_per_flag)


def extract_flag_details(line, details_per_flag):
    match = INCOMPATIBLE_FLAG_LINE_PATTERN.match(line)
    if match:
        flag = match.group("flag")
        if details_per_flag.get(flag, (None, None)) == (None, None):
            details_per_flag[flag] = FlagDetails(
                bazel_version=match.group("version"), issue_url=match.group("url")
            )

        return flag


def get_html_link_text(content, link):
    return f'<a href="{link}" target="_blank">{content}</a>'


# Check if any of the given jobs needs to be migrated by the Bazel team
def needs_bazel_team_migrate(jobs):
    for job in jobs:
        pipeline, _ = get_pipeline_and_platform(job)
        if pipeline in bazelci.DOWNSTREAM_PROJECTS and bazelci.DOWNSTREAM_PROJECTS[pipeline].get(
            "owned_by_bazel"
        ):
            return True
    return False


def print_flags_ready_to_flip(failed_jobs_per_flag, details_per_flag):
    info_text1 = ["#### The following flags didn't break any passing projects"]
    for flag in sorted(list(details_per_flag.keys())):
        if flag not in failed_jobs_per_flag:
            html_link_text = get_html_link_text(":github:", details_per_flag[flag].issue_url)
            info_text1.append(f"* **{flag}** {html_link_text}")

    if len(info_text1) == 1:
        info_text1 = []

    info_text2 = [
        "#### The following flags didn't break any passing Bazel team owned/co-owned projects"
    ]
    for flag, jobs in failed_jobs_per_flag.items():
        if not needs_bazel_team_migrate(jobs.values()):
            failed_cnt = len(jobs)
            s1 = "" if failed_cnt == 1 else "s"
            s2 = "s" if failed_cnt == 1 else ""
            html_link_text = get_html_link_text(":github:", details_per_flag[flag].issue_url)
            info_text2.append(
                f"* **{flag}** {html_link_text}  ({failed_cnt} other job{s1} need{s2} migration)"
            )

    if len(info_text2) == 1:
        info_text2 = []

    print_info("flags_ready_to_flip", "success", info_text1 + info_text2)


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
            "--context=projects_need_migration",
            "--style=error",
            f"\n{info_str}\n",
        ]
    )


def print_flags_need_to_migrate(failed_jobs_per_flag, details_per_flag):
    # The info box printed later is above info box printed before,
    # so reverse the flag list to maintain the same order.
    printed_flag_boxes = False
    for flag in sorted(list(failed_jobs_per_flag.keys()), reverse=True):
        jobs = failed_jobs_per_flag[flag]
        if jobs:
            github_url = details_per_flag[flag].issue_url
            info_text = [f"* **{flag}** " + get_html_link_text(":github:", github_url)]
            jobs_per_pipeline = merge_jobs(jobs.values())
            for pipeline, platforms in jobs_per_pipeline.items():
                bazel_mark = ""
                if pipeline in bazelci.DOWNSTREAM_PROJECTS and bazelci.DOWNSTREAM_PROJECTS[
                    pipeline
                ].get("owned_by_bazel"):
                    bazel_mark = ":bazel:"
                platforms_text = ", ".join(platforms)
                info_text.append(f"  - {bazel_mark}**{pipeline}**: {platforms_text}")
            # Use flag as the context so that each flag gets a different info box.
            print_info(flag, "error", info_text)
            printed_flag_boxes = True
    if not printed_flag_boxes:
        return
    info_text = [
        "#### Downstream projects need to migrate for the following flags:",
        "Projects marked with :bazel: need to be migrated by the Bazel team.",
    ]
    print_info("flags_need_to_migrate", "error", info_text)


def merge_jobs(jobs):
    jobs_per_pipeline = collections.defaultdict(list)
    for job in sorted(jobs, key=lambda s: s["name"].lower()):
        pipeline, platform = get_pipeline_and_platform(job)
        jobs_per_pipeline[pipeline].append(get_html_link_text(platform, job["web_url"]))
    return jobs_per_pipeline


def merge_and_format_jobs(jobs, line_pattern):
    # Merges all jobs for a single pipeline into one line.
    # Example:
    #   pipeline (platform1)
    #   pipeline (platform2)
    #   pipeline (platform3)
    # with line_pattern ">> {}: {}" becomes
    #   >> pipeline: platform1, platform2, platform3
    jobs_per_pipeline = merge_jobs(jobs)
    return [
        line_pattern.format(pipeline, ", ".join(platforms))
        for pipeline, platforms in jobs_per_pipeline.items()
    ]


def get_pipeline_and_platform(job):
    name = job["name"]
    platform = ""
    for p in bazelci.PLATFORMS.values():
        platform_label = p.get("emoji-name")
        if platform_label in name:
            platform = platform_label
            name = name.replace(platform_label, "")
            break

    name = name.partition("-")[0].partition("(")[0].strip()
    return name, platform


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


def analyze_logs(build_number, client):
    build_info = client.get_build_info(build_number)

    already_failing_jobs = []

    # dict(flag name -> dict(job id -> job))
    failed_jobs_per_flag = collections.defaultdict(dict)
    # dict(flag name -> (Bazel version where it's flipped, GitHub issue URL))
    details_per_flag = {}

    threads = []
    for job in build_info["jobs"]:
        # Some irrelevant job has no "state" field
        if "state" in job:
            thread = LogFetcher(job, client)
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()
        process_build_log(
            failed_jobs_per_flag, already_failing_jobs, thread.log, thread.job, details_per_flag
        )

    return already_failing_jobs, failed_jobs_per_flag, details_per_flag


def handle_already_flipped_flags(failed_jobs_per_flag, details_per_flag):
    # Process and remove all flags that have already been flipped.
    # Bazelisk may return already flipped flags if a project uses an old Bazel version
    # via its .bazelversion file.
    current_major_version = get_bazel_major_version()
    failed_jobs_for_new_flags = {}
    details_for_new_flags = {}

    for flag, details in details_per_flag.items():
        if not details.bazel_version or details.bazel_version < current_major_version:
            # TOOD(fweikert): maybe display a Buildkite annotation
            bazelci.eprint(
                "Ignoring {} since it has already been flipped in Bazel {} (latest is {}).".format(
                    flag, details.bazel_version, current_major_version
                )
            )
            continue

        details_for_new_flags[flag] = details
        if flag in failed_jobs_per_flag:
            failed_jobs_for_new_flags[flag] = failed_jobs_per_flag[flag]

    return failed_jobs_for_new_flags, details_for_new_flags


def get_bazel_major_version():
    # Get bazel major version on CI, eg. 0.21 from "Build label: 0.21.0\n..."
    output = subprocess.check_output(
        ["bazel", "--nomaster_bazelrc", "--bazelrc=/dev/null", "version"]
    ).decode("utf-8")
    return output.split()[2].rsplit(".", 1)[0]


def print_result_info(already_failing_jobs, failed_jobs_per_flag, details_per_flag):
    print_flags_need_to_migrate(failed_jobs_per_flag, details_per_flag)

    print_projects_need_to_migrate(failed_jobs_per_flag)

    print_already_fail_jobs(already_failing_jobs)

    print_flags_ready_to_flip(failed_jobs_per_flag, details_per_flag)

    return bool(failed_jobs_per_flag)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Script to aggregate `bazelisk --migrate` test result for incompatible flags and generate pretty Buildkite info messages."
    )
    parser.add_argument("--build_number", type=str)
    parser.add_argument("--notify", type=bool, nargs="?", const=True)

    args = parser.parse_args(argv)
    try:
        if args.build_number:
            client = bazelci.BuildkiteClient(org=BUILDKITE_ORG, pipeline=PIPELINE)
            already_failing_jobs, failed_jobs_per_flag, details_per_flag = analyze_logs(
                args.build_number, client
            )
            failed_jobs_per_flag, details_per_flag = handle_already_flipped_flags(
                failed_jobs_per_flag, details_per_flag
            )
            migration_required = print_result_info(
                already_failing_jobs, failed_jobs_per_flag, details_per_flag
            )

            if migration_required and FAIL_IF_MIGRATION_REQUIRED:
                bazelci.eprint("Exiting with code 3 since a migration is required.")
                return 3
        else:
            parser.print_help()
            return 2

    except bazelci.BuildkiteException as e:
        bazelci.eprint(str(e))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
