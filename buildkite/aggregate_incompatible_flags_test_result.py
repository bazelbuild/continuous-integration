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
import sys
import threading

import bazelci

BUILDKITE_ORG = os.environ["BUILDKITE_ORGANIZATION_SLUG"]

PIPELINE = os.environ["BUILDKITE_PIPELINE_SLUG"]

FAIL_IF_MIGRATION_REQUIRED = os.environ.get("USE_BAZELISK_MIGRATE", "").upper() == "FAIL"

FLAG_LINE_PATTERN = re.compile(r"\s*(?P<flag>--\S+)\s*")

MODULE_VERSION_PATTERN = re.compile(r'(?P<module_version>[a-z](?:[a-z0-9._-]*[a-z0-9])?@[^\s]+)')

BAZEL_TEAM_OWNED_MODULES = frozenset([
    "bazel-skylib",
    "rules_android",
    "rules_android_ndk",
    "rules_cc",
    "rules_java",
    "rules_license",
    "rules_pkg",
    "rules_platform",
    "rules_shell",
    "rules_testing",
])

PROJECT = "module" if PIPELINE == "bcr-bazel-compatibility-test" else "project"

MAX_LOG_FETCHER_THREADS = 10
LOG_FETCHER_SEMAPHORE = threading.Semaphore(MAX_LOG_FETCHER_THREADS)

class LogFetcher(threading.Thread):
    def __init__(self, job, client):
        threading.Thread.__init__(self)
        self.job = job
        self.client = client
        self.log = None

    def run(self):
        with LOG_FETCHER_SEMAPHORE:
            self.log = self.client.get_build_log(self.job, retries = 10)


def process_build_log(failed_jobs_per_flag, already_failing_jobs, log, job):
    if job["state"] == "passed" and "Success: No migration needed." in log:
        return

    if "Failure: Command failed, even without incompatible flags." in log:
        already_failing_jobs.append(job)

    def handle_failing_flags(line):
        flag = extract_flag(line)
        if flag:
            failed_jobs_per_flag[flag][job["id"]] = job

    # bazelisk --migrate might run for multiple times for run / build / test,
    # so there could be several "+++ Result" sections.
    found_result = False
    while "+++ Result" in log:
        found_result = True
        index_success = log.rfind("Command was successful with the following flags:")
        index_failure = log.rfind("Migration is needed for the following flags:")
        if index_success == -1 or index_failure == -1:
            raise bazelci.BuildkiteException("Cannot recognize log of " + job["web_url"])
        for line in log[index_failure:].split("\n"):
            # Strip out BuildKite timestamp prefix
            line = re.sub(r'\x1b.*?\x07', '', line.strip())
            if not line:
                break
            handle_failing_flags(line)
        log = log[0 : log.rfind("+++ Result")]

    # If no "+++ Result" was found, the job must have failed for other reasons
    if not found_result:
        already_failing_jobs.append(job)


def extract_module_version(line):
    match = MODULE_VERSION_PATTERN.search(line)
    if match:
        return match.group("module_version")


def extract_flag(line):
    match = FLAG_LINE_PATTERN.match(line)
    if match:
        return match.group("flag")


def get_html_link_text(content, link):
    return f'<a href="{link}" target="_blank">{content}</a>'


def is_project_owned_by_bazel_team(project):
    if bazelci.is_downstream_pipeline() and project in bazelci.DOWNSTREAM_PROJECTS and bazelci.DOWNSTREAM_PROJECTS[project].get(
        "owned_by_bazel"
    ):
        # Check the downstream projects definition.
        return True
    elif project.split("@")[0] in BAZEL_TEAM_OWNED_MODULES:
        # Parse the module name and check if it's bazel team owned.
        return True
    return False

# Check if any of the given jobs needs to be migrated by the Bazel team
def needs_bazel_team_migrate(jobs):
    for job in jobs:
        project = get_project_name(job)
        if is_project_owned_by_bazel_team(project):
            return True
    return False


def print_flags_ready_to_flip(failed_jobs_per_flag, incompatible_flags):
    info_text1 = [f"#### The following flags didn't break any passing {PROJECT}s"]
    for flag in sorted(list(incompatible_flags.keys())):
        if flag not in failed_jobs_per_flag:
            html_link_text = get_html_link_text(":github:", incompatible_flags[flag])
            info_text1.append(f"* **{flag}** {html_link_text}")

    if len(info_text1) == 1:
        info_text1 = []

    info_text2 = [
        f"#### The following flags didn't break any passing Bazel team owned/co-owned {PROJECT}s"
    ]
    for flag, jobs in failed_jobs_per_flag.items():
        if flag not in incompatible_flags:
            continue
        if not needs_bazel_team_migrate(jobs.values()):
            failed_cnt = len(jobs)
            s1 = "" if failed_cnt == 1 else "s"
            s2 = "s" if failed_cnt == 1 else ""
            html_link_text = get_html_link_text(":github:", incompatible_flags[flag])
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
    info_text = [f"#### The following {PROJECT}s need migration"]
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
        project = get_project_name(job)
        projects.add(project)
    project_num = len(projects)

    s1 = "" if project_num == 1 else "s"
    s2 = "s" if project_num == 1 else ""
    info_text.append(
        f"<details><summary>{project_num} {PROJECT}{s1} need{s2} migration, click to see details</summary><ul>"
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


def print_flags_need_to_migrate(failed_jobs_per_flag, incompatible_flags):
    # The info box printed later is above info box printed before,
    # so reverse the flag list to maintain the same order.
    printed_flag_boxes = False
    for flag in sorted(list(failed_jobs_per_flag.keys()), reverse=True):
        if flag not in incompatible_flags:
            continue
        jobs = failed_jobs_per_flag[flag]
        if jobs:
            github_url = incompatible_flags[flag]
            info_text = [f"* **{flag}** " + get_html_link_text(":github:", github_url)]
            jobs_per_project = merge_jobs(jobs.values())
            for project, platforms in jobs_per_project.items():
                bazel_mark = ""
                if is_project_owned_by_bazel_team(project):
                    bazel_mark = ":bazel:"
                platforms_text = ", ".join(platforms)
                info_text.append(f"  - {bazel_mark}**{project}**: {platforms_text}")
            # Use flag as the context so that each flag gets a different info box.
            print_info(flag, "error", info_text)
            printed_flag_boxes = True
    if not printed_flag_boxes:
        return
    info_text = [
        "#### Projects need to migrate for the following flags:",
        "Projects marked with :bazel: need to be migrated by the Bazel team.",
    ]
    print_info("flags_need_to_migrate", "error", info_text)


def merge_jobs(jobs):
    jobs_per_project = collections.defaultdict(list)
    for job in sorted(jobs, key=lambda s: s["name"].lower()):
        project = get_project_name(job)
        platform_label = get_platform_emoji_name(job)
        jobs_per_project[project].append(get_html_link_text(platform_label, job["web_url"]))
    return jobs_per_project


def merge_and_format_jobs(jobs, line_pattern):
    # Merges all jobs for a single project into one line.
    # Example:
    #   project (platform1)
    #   project (platform2)
    #   project (platform3)
    # with line_pattern ">> {}: {}" becomes
    #   >> project: platform1, platform2, platform3
    jobs_per_project = merge_jobs(jobs)
    return [
        line_pattern.format(project, ", ".join(platforms))
        for project, platforms in jobs_per_project.items()
    ]


def get_project_name(job):
    # Strip out platform label from job name
    name = job["name"].replace(get_platform_emoji_name(job), "")
    if bazelci.is_downstream_pipeline():
        # This is for downstream pipeline, parse the pipeline name
        return name.partition("-")[0].partition("(")[0].strip()
    else:
        # This is for BCR compatibility test pipeline, parse the module name + version
        return extract_module_version(name)


def get_platform_emoji_name(job):
    # By search for the platform label in the job name.
    name = job["name"]
    for p in bazelci.PLATFORMS.values():
        platform_label = p.get("emoji-name")
        if platform_label in name:
            return platform_label
    raise bazelci.BuildkiteException("Cannot detect platform name for: " + job["web_url"])


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

    threads = []
    for job in build_info["jobs"]:
        # Some irrelevant job has no "state" or "raw_log_url" field
        if "state" in job and "raw_log_url" in job:
            thread = LogFetcher(job, client)
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()
        process_build_log(
            failed_jobs_per_flag, already_failing_jobs, thread.log, thread.job
        )

    return already_failing_jobs, failed_jobs_per_flag


def print_result_info(already_failing_jobs, failed_jobs_per_flag):
    # key: flag name, value: Github Issue URL
    incompatible_flags = bazelci.fetch_incompatible_flags()

    print_flags_need_to_migrate(failed_jobs_per_flag, incompatible_flags)

    print_projects_need_to_migrate(failed_jobs_per_flag)

    print_already_fail_jobs(already_failing_jobs)

    print_flags_ready_to_flip(failed_jobs_per_flag, incompatible_flags)

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
            already_failing_jobs, failed_jobs_per_flag = analyze_logs(
                args.build_number, client
            )
            migration_required = print_result_info(
                already_failing_jobs, failed_jobs_per_flag
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
