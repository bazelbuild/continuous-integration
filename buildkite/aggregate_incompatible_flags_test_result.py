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
import requests
import sys
import threading

import bazelci

INCOMPATIBLE_FLAGS = bazelci.fetch_incompatible_flags()

BUILDKITE_ORG = os.environ["BUILDKITE_ORGANIZATION_SLUG"]

PIPELINE = os.environ["BUILDKITE_PIPELINE_SLUG"]

FAIL_IF_MIGRATION_REQUIRED = os.environ.get("USE_BAZELISK_MIGRATE", "").upper() == "FAIL"

REPO_PATTERN = re.compile(r"https?://github.com/(?P<owner>[^/]+)/(?P<repo>[^/]+).git")

EMOJI_PATTERN = re.compile(r":([\w+-]+):")

EMOJI_IMAGE_TEMPLATE = '<img src="https://raw.githubusercontent.com/buildkite/emojis/master/img-buildkite-64/{}.png" height="16"/>'

INCOMPATIBLE_FLAG_LINE_PATTERN = re.compile(
    r"\s*(?P<flag>--incompatible_\S+)\s*(\(Bazel\s+(?P<version>[^:]+):\s+(?P<url>[^\)]+)\))?"
)

ISSUE_TEMPLATE = """Incompatible flag {flag} will be enabled by default in Bazel {version}, thus breaking {project}.

The flag is documented here: {issue_url}

Please check the following CI builds for build and test results:

{links}

Never heard of incompatible flags before? We have [documentation](https://docs.bazel.build/versions/master/backward-compatibility.html) that explains everything.

If you don't want to receive any future issues for {project} or if you have any questions,
please file an issue in https://github.com/bazelbuild/continuous-integration

**Important**: Please do NOT modify the issue title since that might break our tools.
"""

GITHUB_ISSUE_REPORTER = "bazel-flag-bot"

GITHUB_TOKEN_KMS_KEY = "github-api-token"

ENCRYPTED_GITHUB_API_TOKEN = """
CiQA6OLsm2YFaO2fOFkdj3TCxCihvMNmf6HYKWXVSKnfDQtuYEsSUQBsAAJAI9UgPCsJZCQMC+QB/g4eFd
02IGzaOhSuCYyllc9Lr332wYAt7P52vXgmAU1zLfzGsm0iJ1KzjFW82BsYA6rgeSq4dCPTa8csRqND9Q==
""".strip()


FlagDetails = collections.namedtuple("FlagDetails", ["bazel_version", "issue_url"])


class GitHubError(Exception):
    def __init__(self, code, message):
        super(GitHubError, self).__init__("{}: {}".format(code, message))
        self.code = code
        self.message = message


class GitHubIssueClient(object):
    def __init__(self, reporter, oauth_token):
        self._reporter = reporter
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Accept": "application/vnd.github.v3+json",
                "Authorization": "token {}".format(oauth_token),
                "Content-Type": "application/json",
            }
        )

    def get_issue(self, repo_owner, repo_name, title):
        # Returns an arbitrary matching issue if multiple matching issues exist.
        json_data = self._send_request(repo_owner, repo_name, params={"creator": self._reporter})
        for i in json_data:
            if i["title"] == title:
                return i["number"]

    def create_issue(self, repo_owner, repo_name, title, body):
        # TODO(fweikert): Remove once the script is stable (#869)
        repo_owner = "fweikert"
        repo_name = "bugs"

        json_data = self._send_request(
            repo_owner,
            repo_name,
            post=True,
            json={"title": title, "body": body, "assignee": None, "labels": [], "milestone": None},
        )
        return json_data.get("number", "")

    def _send_request(self, repo_owner, repo_name, post=False, **kwargs):
        url = "https://api.github.com/repos/{}/{}/issues".format(repo_owner, repo_name)
        method = self._session.post if post else self._session.get
        response = method(url, **kwargs)
        if response.status_code // 100 != 2:
            raise GitHubError(response.status_code, response.content)

        return response.json()


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

    # bazelisk --migrate might run for multiple times for run / build / test,
    # so there could be several "+++ Result" sections.
    while "+++ Result" in log:
        index_success = log.rfind("Command was successful with the following flags:")
        index_failure = log.rfind("Migration is needed for the following flags:")
        if index_success == -1 or index_failure == -1:
            raise bazelci.BuildkiteException("Cannot recognize log of " + job["web_url"])
        lines = log[index_failure:].split("\n")
        for line in lines:
            match = INCOMPATIBLE_FLAG_LINE_PATTERN.match(line)
            if match:
                flag = match.group("flag")
                failed_jobs_per_flag[flag][job["id"]] = job
                details_per_flag[flag] = FlagDetails(
                    bazel_version=match.group("version"), issue_url=match.group("url")
                )
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
    printed_flag_boxes = False
    for flag in sorted(list(failed_jobs_per_flag.keys()), reverse=True):
        jobs = failed_jobs_per_flag[flag]
        if jobs:
            github_url = INCOMPATIBLE_FLAGS[flag]
            info_text = [f"* **{flag}** " + get_html_link_text(":github:", github_url)]
            info_text += merge_and_format_jobs(jobs.values(), "  - **{}**: {}")
            # Use flag as the context so that each flag gets a different info box.
            print_info(flag, "error", info_text)
            printed_flag_boxes = True
    if not printed_flag_boxes:
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


def print_result_info(already_failing_jobs, failed_jobs_per_flag):
    print_flags_need_to_migrate(failed_jobs_per_flag)

    print_projects_need_to_migrate(failed_jobs_per_flag)

    print_already_fail_jobs(already_failing_jobs)

    print_flags_ready_to_flip(failed_jobs_per_flag)

    return bool(failed_jobs_per_flag)


def notify_projects(failed_jobs_per_flag, details_per_flag):
    links_per_project_and_flag = collect_notification_links(failed_jobs_per_flag)
    create_all_issues(details_per_flag, links_per_project_and_flag)


def collect_notification_links(failed_jobs_per_flag):
    links_per_project_and_flag = collections.defaultdict(set)
    for flag, job_data in failed_jobs_per_flag.items():
        for job in job_data.values():
            project_label, platform = get_pipeline_and_platform(job)
            link = get_link_for_build(platform, job["web_url"])
            links_per_project_and_flag[(project_label, flag)].add(link)

    return links_per_project_and_flag


def get_link_for_build(platform, url):
    names = [v["name"] for v in bazelci.PLATFORMS.values() if v["emoji-name"] == platform]
    display_name = names[0] if names else ""

    match = EMOJI_PATTERN.search(platform)
    img = EMOJI_IMAGE_TEMPLATE.format(match.group(1)) if match else ""

    text = (img + display_name) or platform
    return get_html_link_text(text, url)


def create_all_issues(details_per_flag, links_per_project_and_flag):
    errors = []
    issue_client = get_github_client()
    for (project_label, flag), links in links_per_project_and_flag.items():
        try:
            details = details_per_flag.get(flag, (None, None))
            if details.bazel_version in (None, "unreleased binary"):
                raise bazelci.BuildkiteException(
                    "Notifications: Invalid Bazel version '{}' for flag {}".format(
                        details.bazel_version or "", flag
                    )
                )

            if not details.issue_url:
                raise bazelci.BuildkiteException(
                    "Notifications: Missing GitHub issue URL for flag {}".format(flag)
                )

            repo_owner, repo_name, do_not_notify = get_project_details(project_label)
            if do_not_notify:
                bazelci.eprint("{} has opted out of notifications.".format(project_label))
                continue

            title = get_issue_title(project_label, details.bazel_version, flag)
            if issue_client.get_issue(repo_owner, repo_name, title):
                bazelci.eprint(
                    "There is already an issue in {}/{} for project {}, flag {} and Bazel {}".format(
                        repo_owner, repo_name, project_label, flag, details.bazel_version
                    )
                )
            else:
                body = create_issue_body(project_label, flag, details, links)
                issue_client.create_issue(repo_owner, repo_name, title, body)
        except (bazelci.BuildkiteException, GitHubError) as ex:
            errors.append("Could not notify project '{}': {}".format(project_label, ex))

    if errors:
        print_info("notify_errors", "error", errors)


def get_github_client():
    try:
        github_token = bazelci.decrypt_token(
            encrypted_token=ENCRYPTED_GITHUB_API_TOKEN, kms_key=GITHUB_TOKEN_KMS_KEY
        )
    except Exception as ex:
        raise bazelci.BuildkiteException("Failed to decrypt GitHub API token: {}".format(ex))

    return GitHubIssueClient(reporter=GITHUB_ISSUE_REPORTER, oauth_token=github_token)


def get_project_details(project_label):
    entry = bazelci.DOWNSTREAM_PROJECTS.get(project_label, {})
    full_repo = entry.get("git_repository", "")
    if not full_repo:
        raise bazelci.BuildkiteException(
            "Could not retrieve Git repository for project '{}'".format(project_label)
        )
    match = REPO_PATTERN.match(full_repo)
    if not match:
        raise bazelci.BuildkiteException(
            "Hosts other than GitHub are currently not supported ({})".format(full_repo)
        )

    return match.group("owner"), match.group("repo"), entry.get("do_not_notify", False)


def get_issue_title(project_label, bazel_version, flag):
    return "Flag {} will break {} in Bazel {}".format(flag, project_label, bazel_version)


def create_issue_body(project_label, flag, details, links):
    return ISSUE_TEMPLATE.format(
        project=project_label,
        version=details.bazel_version,
        issue_url=details.issue_url,
        flag=flag,
        links="\n".join("* {}".format(l) for l in links),
    )


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
            migration_required = print_result_info(already_failing_jobs, failed_jobs_per_flag)

            if args.notify:
                notify_projects(failed_jobs_per_flag, details_per_flag)

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
