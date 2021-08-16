#!/usr/bin/env python3
#
# Copyright 2020 The Bazel Authors. All rights reserved.
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

import sys
import threading

import bazelci

BUILDKITE_ORG = "bazel"
DOWNSTREAM_PIPELINE = "bazel-at-head-plus-downstream"
CULPRIT_FINDER_PIPELINE = "culprit-finder"

COLORS = {
    "SERIOUS" : '\033[95m',
    "HEADER" : '\033[34m',
    "PASSED" : '\033[92m',
    "WARNING" : '\033[93m',
    "FAIL" : '\033[91m',
    "ENDC" : '\033[0m',
    "INFO" : '\033[0m',
    "BOLD" : '\033[1m',
}

DOWNSTREAM_PIPELINE_CLIENT = bazelci.BuildkiteClient(BUILDKITE_ORG, DOWNSTREAM_PIPELINE)
CULPRIT_FINDER_PIPELINE_CLIENT = bazelci.BuildkiteClient(BUILDKITE_ORG, CULPRIT_FINDER_PIPELINE)

def print_info(context, style, info, append=True):
    info_str = "\n".join(info)
    bazelci.execute_command(
        args = [
            "buildkite-agent",
            "annotate",
        ] + (["--append"] if append else []) + [
            f"--context={context}",
            f"--style={style}",
            f"\n{info_str}\n",
        ],
        print_output = False,
    )


# The class to fetch build result and do the analysis
# The build result are stored in main_result and downstream_result, their structures are like:
# 1. An example of downstream _result
# {
#     "build_number": 1396,
#     "bazel_commit": "83c5bb00b59137effd976e4f510f74613d85ee1c",
#     "commit": "e2b6e2cffc79b89cf0840499c30e3818aaa9ee4b",
#     "state": "passed",
#     "tasks": {
#         "ubuntu1604": {
#             "id": "ba3b744c-536d-4f7b-ad9a-c2edd8839ba1",
#             "name": "Android Studio Plugin (:ubuntu: 16.04 (OpenJDK 8))",
#             "state": "passed",
#             "web_url": "https://buildkite.com/bazel/bazel-at-head-plus-downstream/builds/1396#ba3b744c-536d-4f7b-ad9a-c2edd8839ba1"
#         }
#     }
# }
# 2. An example of main_result
# {
#     "build_number": 6299,
#     "commit": "e2b6e2cffc79b89cf0840499c30e3818aaa9ee4b",
#     "last_green_commit": "e2b6e2cffc79b89cf0840499c30e3818aaa9ee4b",
#     "state": "passed",
#     "tasks": {
#         "ubuntu1604": {
#             "id": "1333fa60-c26f-45dd-9169-eeb9a7cc9add",
#             "name": ":ubuntu: 16.04 (OpenJDK 8)",
#             "state": "passed",
#             "web_url": "https://buildkite.com/bazel/android-studio-plugin/builds/6299#1333fa60-c26f-45dd-9169-eeb9a7cc9add"
#         }
#     }
# }
class BuildInfoAnalyzer(threading.Thread):

    success_log_lock = threading.Lock()
    success_log = []

    def __init__(self, project, pipeline, downstream_result):
        super().__init__()
        self.project = project
        self.pipeline = pipeline
        self.downstream_result = downstream_result
        self.main_result = None
        self.client = bazelci.BuildkiteClient(BUILDKITE_ORG, pipeline)
        self.analyze_log = [f"{COLORS['HEADER']}Analyzing {self.project}: {COLORS['ENDC']}"]
        self.broken_by_infra = False


    def _get_main_build_result(self):
        build_info_list = self.client.get_build_info_list([
            ("branch", "master"),
            ("page", "1"),
            ("per_page", "1"),
            ("state[]", "failed"),
            ("state[]", "passed"),
        ])
        if not build_info_list:
            error = f"Cannot find finished build for pipeline {self.pipeline}, please try to rerun the pipeline first."
            self._log("SERIOUS", error)
            raise bazelci.BuildkiteException(error)
        main_build_info = build_info_list[0]

        self.main_result = {}
        self.main_result["commit"] = main_build_info["commit"]
        self.main_result["build_number"] = main_build_info["number"]
        job_infos = filter(lambda x: bool(x), (extract_job_info_by_key(job) for job in main_build_info["jobs"]))
        self.main_result["tasks"] = group_job_info_by_task(job_infos)
        self.main_result["state"] = get_project_state(self.main_result["tasks"])

        last_green_commit_url = bazelci.bazelci_last_green_commit_url(
            bazelci.DOWNSTREAM_PROJECTS[self.project]["git_repository"], self.pipeline
        )
        self.main_result["last_green_commit"] = bazelci.get_last_green_commit(last_green_commit_url)


    # Log all succeeded projects in the same annotate block
    def _log_success(self, text):
        with BuildInfoAnalyzer.success_log_lock:
            BuildInfoAnalyzer.success_log.append(f"{COLORS['HEADER']}Analyzing {self.project}: {COLORS['PASSED']}{text}{COLORS['ENDC']}")
            info = [
                "<details><summary><strong>:bk-status-passed: Success</strong></summary><p>",
                "",
                "```term",
            ] + BuildInfoAnalyzer.success_log + [
                "```",
                "",
                "</p></details>"
            ]
            print_info("success-info", "success", info, append = False)

    # Log broken projects in their separate annotate block
    def _log(self, c, text):
        self.analyze_log.append(f"{COLORS[c]}{text}{COLORS['ENDC']}")
        info = [
            f"<details><summary><strong>:bk-status-failed: {self.project}</strong></summary><p>",
            "",
            "```term",
        ] + self.analyze_log + [
            "```",
            "",
            "</p></details>"
        ]
        print_info(self.pipeline, "warning", info, append = False)


    # Implement the log function so that it can be called from BuildkiteClient
    def log(self, text):
        # Be smart here to reduce log length.
        if self.analyze_log[-1].startswith(COLORS["INFO"] + "Waiting for "):
            self.analyze_log.pop(-1)
        self._log("INFO", text)


    def _trigger_bisect(self, tasks):
        env = {
            "PROJECT_NAME": self.project,
            "TASK_NAME_LIST": ",".join(tasks) if tasks else "",
        }
        return CULPRIT_FINDER_PIPELINE_CLIENT.trigger_new_build("HEAD", f"Bisecting {self.project}", env)


    # Search for certain message in the log to determine the bisect result.
    # Return values are
    #   1. A bisect result message
    #   2. The commit of the culprit if found, otherwise None
    def _determine_bisect_result(self, job):
        bisect_log = CULPRIT_FINDER_PIPELINE_CLIENT.get_build_log(job)
        pos = bisect_log.rfind("first bad commit is ")
        if pos != -1:
            start = pos + len("first bad commit is ")
            # The length of a full commit hash is 40
            culprit_commit = bisect_log[start:start + 40]
            return "\n".join([
                 "Culprit found!",
                 bisect_log[pos:].replace("\r", ""),
                 "Bisect URL: " + job["web_url"],
            ]), culprit_commit
        pos = bisect_log.rfind("Given good commit")  # Matching "Given good commit (XXXX) is not actually good, abort bisecting."
        if pos != -1:
            self.broken_by_infra = True
            return "\n".join([
                "Given good commit is now failing. This is probably caused by remote cache issue or infra change.",
                "Please ping philwo@ or pcloudy@ for investigation.",
                "Bisect URL: " + job["web_url"],
            ]), None
        pos = bisect_log.rfind("first bad commit not found, every commit succeeded.")
        if pos != -1:
            return "\n".join([
                "Bisect didn't manage to reproduce the failure, all builds succeeded.",
                "Maybe the build are cached from previous build with a different Bazel version or it could be flaky.",
                "Please try to rerun the bisect with NEEDS_CLEAN=1 and REPEAT_TIMES=3.",
                "Bisect URL: " + job["web_url"],
            ]), None
        return "Bisect failed due to unknown reason, please check " + job["web_url"], None


    def _retry_failed_jobs(self, build_result, buildkite_client):
        retry_per_failed_task = {}
        for task, info in build_result["tasks"].items():
            if info["state"] != "passed":
                retry_per_failed_task[task] = buildkite_client.trigger_job_retry(build_result["build_number"], info["id"])
        for task, job_info in retry_per_failed_task.items():
            retry_per_failed_task[task] = buildkite_client.wait_job_to_finish(build_number = build_result["build_number"], job_id = job_info["id"], logger = self)
        return retry_per_failed_task


    def _print_job_list(self, jobs):
        for job in jobs:
            self._log("INFO", f"  {job['name']}: {job['web_url']}")
        self._log("INFO", "")


    def _analyze_main_pipeline_result(self):
        self._log("INFO", "")
        self._log("PASSED", "***Analyze failures in main pipeline***")

        # Report failed tasks
        self._log("WARNING", "The following tasks are failing in main pipeline")
        self._print_job_list([info for _, info in self.main_result["tasks"].items() if info["state"] != "passed"])

        # Retry all failed tasks
        self._log("PASSED", "Retry failed main pipeline tasks...")
        retry_per_failed_task = self._retry_failed_jobs(self.main_result, self.client)

        # Report tasks that succeeded after retry
        succeeded_tasks = []
        for task, info in retry_per_failed_task.items():
            if info["state"] == "passed":
                succeeded_tasks.append(info)
                self.main_result["tasks"][task]["flaky"] = True
        if succeeded_tasks:
            self._log("WARNING", "The following tasks succeeded after retry, they might be flaky")
            self._print_job_list(succeeded_tasks)

        # Report tasks that are still failing after retry
        still_failing_tasks = []
        for task, info in retry_per_failed_task.items():
            if info["state"] != "passed":
                still_failing_tasks.append(info)
                self.main_result["tasks"][task]["broken"] = True
        if still_failing_tasks:
            last_green_commit = self.main_result["last_green_commit"]
            self._log("FAIL", f"The following tasks are still failing after retry, they are probably broken due to changes from the project itself.")
            self._log("FAIL", f"The last recorded green commit is {last_green_commit}. Please file bug for the repository.")
            self._print_job_list(still_failing_tasks)


    def _analyze_for_downstream_pipeline_result(self):
        self._log("INFO", "")
        self._log("PASSED", "***Analyze failures in downstream pipeline***")

        # Report failed tasks
        self._log("WARNING", "The following tasks are failing in downstream pipeline")
        self._print_job_list([info for _, info in self.downstream_result["tasks"].items() if info["state"] != "passed"])

        # Retry all failed tasks
        self._log("PASSED", "Retry failed downstream pipeline tasks...")
        retry_per_failed_task = self._retry_failed_jobs(self.downstream_result, DOWNSTREAM_PIPELINE_CLIENT)

        # Report tasks that succeeded after retry
        succeeded_tasks = []
        for task, info in retry_per_failed_task.items():
            if info["state"] == "passed":
                succeeded_tasks.append(info)
                self.downstream_result["tasks"][task]["flaky"] = True
        if succeeded_tasks:
            self._log("WARNING", "The following tasks succeeded after retry, they might be flaky")
            self._print_job_list(succeeded_tasks)

        # Report tasks that are still failing after retry
        still_failing_tasks = []
        failing_task_names = []
        for task, info in retry_per_failed_task.items():
            if info["state"] != "passed":
                still_failing_tasks.append(info)
                failing_task_names.append(task)
                self.downstream_result["tasks"][task]["broken"] = True

        if not still_failing_tasks:
            return

        self._log("FAIL", f"The following tasks are still failing after retry, they are probably broken due to recent Bazel changes.")
        self._print_job_list(still_failing_tasks)

        # Do bisect for still failing jobs
        self._log("PASSED", f"Bisect for still failing tasks...")
        bisect_build = self._trigger_bisect(failing_task_names)
        bisect_build = CULPRIT_FINDER_PIPELINE_CLIENT.wait_build_to_finish(build_number = bisect_build["number"], logger = self)
        bisect_result_by_task = {}
        for task in failing_task_names:
            for job in bisect_build["jobs"]:
                if ("--task_name=" + task) in job["command"]:
                    bisect_result_by_task[task], culprit = self._determine_bisect_result(job)
                    if culprit:
                        self.downstream_result["tasks"][task]["culprit"] = culprit
            if task not in bisect_result_by_task:
                error = f"Bisect job for task {task} is missing in " + bisect_build["web_url"]
                self._log("SERIOUS", error)
                raise bazelci.BuildkiteException(error)

        # Report bisect result
        for task, result in bisect_result_by_task.items():
            self._log("WARNING", "Bisect result for " + self.downstream_result["tasks"][task]["name"])
            self._log("INFO", result)


    def _analyze(self):
        # Main build: PASSED; Downstream build: PASSED
        if self.main_result["state"] == "passed" and self.downstream_result["state"] == "passed":
            self._log_success("Main build: PASSED; Downstream build: PASSED")
            return

        # Main build: FAILED; Downstream build: PASSED
        if self.main_result["state"] == "failed" and self.downstream_result["state"] == "passed":
            self._log("FAIL", "Main build: FAILED")
            self._log("PASSED", "Downstream build: PASSED")
            self._analyze_main_pipeline_result()
            self._log("HEADER", "Analyzing finished.")
            return

        # Main build: PASSED; Downstream build: FAILED
        if self.main_result["state"] == "passed" and self.downstream_result["state"] == "failed":
            self._log("PASSED", "Main build: PASSED")
            self._log("FAIL", "Downstream build: FAILED")
            self._analyze_for_downstream_pipeline_result()
            self._log("HEADER", "Analyzing finished.")
            return

        # Main build: FAILED; Downstream build: FAILED
        if self.main_result["state"] == "failed" and self.downstream_result["state"] == "failed":
            self._log("FAIL", "Main build: FAILED")
            self._log("FAIL", "Downstream build: FAILED")

            last_green_commit = self.main_result["last_green_commit"]

            # If the lastest build is the last green commit, that means some infra change has caused the breakage.
            if last_green_commit == self.main_result["commit"]:
                self.broken_by_infra = True
                self._log("SERIOUS", f"Project failed at last green commit. This is probably caused by an infra change, please ping philwo@ or pcloudy@.")
                self._log("HEADER", "Analyzing finished.")
                return

            # Rebuild the project at last green commit, check if the failure is caused by infra change.
            self._log("PASSED", f"Rebuild at last green commit {last_green_commit}...")
            build_info = self.client.trigger_new_build(last_green_commit, "Trigger build at last green commit.")
            build_info = self.client.wait_build_to_finish(build_number = build_info["number"], logger = self)

            if build_info["state"] == "failed":
                self.broken_by_infra = True
                self._log("SERIOUS", f"Project failed at last green commit. This is probably caused by an infra change, please ping philwo@ or pcloudy@.")
            elif build_info["state"] == "passed":
                self._log("PASSED", f"Project succeeded at last green commit. Maybe main pipeline and downstream pipeline are broken for different reasons.")
                self._analyze_main_pipeline_result()
                self._analyze_for_downstream_pipeline_result()
            else:
                self._log("SERIOUS", f"Rebuilding project at last green commit failed with unknown reason. Please check " + build_info["web_url"])
            self._log("HEADER", "Analyzing finished.")
            return


    def run(self):
        self._get_main_build_result()
        self._analyze()


def get_html_link_text(content, link):
    return f'<a href="{link}" target="_blank">{content}</a>'


def add_tasks_info_text(tasks_per_project, info_text):
    for project, task_list in tasks_per_project.items():
        html_link_text = ", ".join([get_html_link_text(name, url) for name, url in task_list])
        info_text.append(f"* **{project}**: {html_link_text}")


def collect_tasks_by_key(build_result, project_name, tasks_per_project, key):
    for task_info in build_result["tasks"].values():
        if task_info.get(key):
            if project_name not in tasks_per_project:
                tasks_per_project[project_name] = []
            tasks_per_project[project_name].append((task_info["name"], task_info["web_url"]))


def get_bazel_commit_url(commit):
    return f"https://github.com/bazelbuild/bazel/commit/{commit}"


def get_buildkite_pipeline_url(pipeline):
    return f"https://buildkite.com/bazel/{pipeline}"


def report_infra_breakages(analyzers):
    projects_broken_by_infra = [(analyzer.project, analyzer.pipeline) for analyzer in analyzers if analyzer.broken_by_infra]

    if not projects_broken_by_infra:
        return

    info_text = [
        "#### The following projects are probably broken by infra change",
        "Check the analyze log for more details.",
    ]
    html_link_text = ", ".join([get_html_link_text(project, get_buildkite_pipeline_url(pipeline)) for project, pipeline in projects_broken_by_infra])
    info_text.append(f"* {html_link_text}")
    print_info("broken_tasks_by_infra", "error", info_text)


def report_downstream_breakages(analyzers):
    broken_downstream_tasks_per_project = {}
    culprits_per_project = {}
    for analyzer in analyzers:
        collect_tasks_by_key(analyzer.downstream_result, analyzer.project, broken_downstream_tasks_per_project, "broken")
        culprits = set()
        for task_info in analyzer.downstream_result["tasks"].values():
            if task_info.get("culprit"):
                culprits.add(task_info["culprit"])
        if culprits:
            culprits_per_project[analyzer.project] = culprits

    if not broken_downstream_tasks_per_project:
        return

    info_text = [
        "#### Broken projects with Bazel at HEAD (Downstream Build)",
        "These projects are probably broken by recent Bazel changes.",
    ]
    for project, task_list in broken_downstream_tasks_per_project.items():
        html_link_text = ", ".join([get_html_link_text(name, url) for name, url in task_list])
        info_text.append(f"* **{project}**: {html_link_text}")
        if project in culprits_per_project:
            culprit_text = ", ".join([get_html_link_text(commit, get_bazel_commit_url(commit)) for commit in culprits_per_project[project]])
            info_text.append(f"  - Culprit Found: {culprit_text}")
        else:
            info_text.append("  - Culprit Not Found: Please check the analyze log for more details")
    print_info("broken_downstream_tasks", "error", info_text)


def report_main_breakages(analyzers):
    broken_main_tasks_per_project = {}
    for analyzer in analyzers:
        collect_tasks_by_key(analyzer.main_result, analyzer.project, broken_main_tasks_per_project, "broken")

    if not broken_main_tasks_per_project:
        return

    info_text = [
        "#### Broken projects with Bazel at latest release (Main Build)",
        "These projects are probably broken by their own changes.",
    ]
    add_tasks_info_text(broken_main_tasks_per_project, info_text)
    print_info("broken_main_tasks", "warning", info_text)


def report_flaky_tasks(analyzers):
    flaky_main_tasks_per_project = {}
    flaky_downstream_tasks_per_project = {}
    for analyzer in analyzers:
        collect_tasks_by_key(analyzer.main_result, analyzer.project, flaky_main_tasks_per_project, "flaky")
        collect_tasks_by_key(analyzer.downstream_result, analyzer.project, flaky_downstream_tasks_per_project, "flaky")

    if not flaky_main_tasks_per_project and not flaky_downstream_tasks_per_project:
        return

    info_text = ["#### Flaky Projects"]

    if flaky_main_tasks_per_project:
        info_text.append("##### Main Build")
        add_tasks_info_text(flaky_main_tasks_per_project, info_text)

    if flaky_downstream_tasks_per_project:
        info_text.append("##### Downstream Build")
        add_tasks_info_text(flaky_downstream_tasks_per_project, info_text)

    print_info("flaky_tasks", "warning", info_text)


def report(analyzers):
    print_info("analyze_log", "info", ["#### Analyze log"])
    report_flaky_tasks(analyzers)
    report_main_breakages(analyzers)
    report_downstream_breakages(analyzers)
    report_infra_breakages(analyzers)


# Get the raw downstream build result from the lastest finished build
def get_latest_downstream_build_info():
    downstream_build_list = DOWNSTREAM_PIPELINE_CLIENT.get_build_info_list([
        ("branch", "master"),
        ("page", "1"),
        ("per_page", "1"),
        ("state[]", "failed"),
        ("state[]", "passed"),
    ])

    if len(downstream_build_list) == 0:
        raise bazelci.BuildkiteException("Cannot find finished downstream build, please try to rerun downstream pipeline first.")
    return downstream_build_list[0]


# Parse infos from command and extract info from original job infos.
# Result is like:
#     [
#         {"task": "A", "state": "passed", "web_url": "http://foo/bar/A"},
#         {"task": "B", "state": "failed", "web_url": "http://foo/bar/B"},
#     ]
def extract_job_info_by_key(job, info_from_command = [], info_from_job = ["name", "state", "web_url", "id"]):
    if "command" not in job or not job["command"] or "bazelci.py runner" not in job["command"]:
        return None

    # We have to know which task this job info belongs to
    if "task" not in info_from_command:
        info_from_command.append("task")

    job_info = {}

    # Assume there is no space in each argument
    args = job["command"].split(" ")
    for info in info_from_command:
        for arg in args:
            prefix = "--" + info + "="
            if arg.startswith(prefix):
                job_info[info] = arg[len(prefix):]
        if info not in job_info:
            return None

    for info in info_from_job:
        if info not in job:
            return None
        job_info[info] = job[info]

    return job_info


# Turn a list of job infos
#     [
#         {"task": "windows", "state": "passed", "web_url": "http://foo/bar/A"},
#         {"task": "macos", "state": "failed", "web_url": "http://foo/bar/B"},
#     ]
# into a map of task name to job info
#     {
#         "windows": {"state": "passed", "web_url": "http://foo/bar/A"},
#         "macos": {"state": "failed", "web_url": "http://foo/bar/B"},
#     }
def group_job_info_by_task(job_infos):
    job_info_by_task = {}
    for job_info in job_infos:
        if "task" not in job_info:
            raise bazelci.BuildkiteException(f"'task' must be a key of job_info: {job_info}")

        task_name = job_info["task"]
        del job_info["task"]
        job_info_by_task[task_name] = job_info

    return job_info_by_task


# If any of the tasks didn't pass, we condsider the state of this project failed.
def get_project_state(tasks):
    for _, infos in tasks.items():
        if infos["state"] != "passed" and infos["state"] != "soft_failed":
            return "failed"
    return "passed"


# Get the downstream build result in a structure like:
# {
#     "project_x" : {
#         "commit": "XXXXXXXX",
#         "bazel_commit": "XXXXXXXX",
#         "tasks" : {
#             "A": {"state": "passed", "web_url": "http://foo/bar/A"},
#             "B": {"state": "failed", "web_url": "http://foo/bar/B"},
#         }
#     }
#     "project_y" : {
#         "commit": "XXXXXXXX",
#         "bazel_commit": "XXXXXXXX",
#         "tasks" : {
#             "C": {"state": "passed", "web_url": "http://foo/bar/C"},
#             "D": {"state": "failed", "web_url": "http://foo/bar/D"},
#         }
#     }
# }
def get_downstream_result_by_project(downstream_build_info):
    config_to_project = {}
    for project_name, project_info in bazelci.DOWNSTREAM_PROJECTS.items():
        config_to_project[project_info["http_config"]] = project_name

    downstream_result = {}
    jobs_per_project = {}

    for job in downstream_build_info["jobs"]:
        job_info = extract_job_info_by_key(job = job, info_from_command = ["http_config", "git_commit"])
        if job_info:
            project_name = config_to_project[job_info["http_config"]]
            if project_name not in downstream_result:
                jobs_per_project[project_name] = []
                downstream_result[project_name] = {}
                downstream_result[project_name]["bazel_commit"] = downstream_build_info["commit"]
                downstream_result[project_name]["build_number"] = downstream_build_info["number"]
                downstream_result[project_name]["commit"] = job_info["git_commit"]
            jobs_per_project[project_name].append(job_info)

    for project_name in jobs_per_project:
        tasks = group_job_info_by_task(jobs_per_project[project_name])
        downstream_result[project_name]["tasks"] = tasks
        downstream_result[project_name]["state"] = get_project_state(tasks)

    return downstream_result


def main(argv=None):
    downstream_build_info = get_latest_downstream_build_info()
    downstream_result = get_downstream_result_by_project(downstream_build_info)

    analyzers = []
    for project_name, project_info in bazelci.DOWNSTREAM_PROJECTS.items():
        if project_name in downstream_result:
            analyzer = BuildInfoAnalyzer(project_name, project_info["pipeline_slug"], downstream_result[project_name])
            analyzers.append(analyzer)
            analyzer.start()

    for analyzer in analyzers:
        analyzer.join()

    report(analyzers)

    return 0

if __name__ == "__main__":
    sys.exit(main())
