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
import os
import sys
import subprocess
import time
import yaml
import bazelci
from bazelci import DOWNSTREAM_PROJECTS
from bazelci import PLATFORMS
from bazelci import BuildkiteException

BAZEL_REPO_DIR = os.getcwd()

def bazel_culprit_finder_py_url():
    """
    URL to the latest version of this script.
    """
    return "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/culprit_finder.py?{}".format(int(time.time()))


def fetch_culprit_finder_py_command():
    return "curl -s {0} -o culprit_finder.py".format(bazel_culprit_finder_py_url())


def get_bazel_commits_between(first_commit, second_commit):
    """
    Get bazel commits between first_commit and second_commit as a list.
    first_commit is not included in the list.
    second_commit is included in the list.
    """
    try:
        os.chdir(BAZEL_REPO_DIR)
        output = subprocess.check_output(["git", "log", "--pretty=tformat:%H", "%s..%s"
                                         % (first_commit, second_commit)])
        return [ i for i in reversed(output.decode("utf-8").split("\n")) if i ]
    except subprocess.CalledProcessError as e:
        raise bazelci.BazelBuildFailedException("Failed to get bazel commits between %s..%s:\n%s"
                                                % (first_commit, second_commit, str(e)))


def test_with_bazel_at_commit(project_name, platform_name, git_repo_location, bazel_commit):
    http_config = DOWNSTREAM_PROJECTS[project_name]["http_config"]
    git_repository = DOWNSTREAM_PROJECTS[project_name]["git_repository"]
    return_code =  bazelci.main(["runner",
                                 "--platform=" + platform_name,
                                 "--http_config=" + http_config,
                                 "--git_repository=" + git_repository,
                                 "--git_repo_location=" + git_repo_location,
                                 "--use_bazel_at_commit=" + bazel_commit])
    return return_code == 0


def clone_git_repository(project_name, platform_name):
    git_repository = DOWNSTREAM_PROJECTS[project_name]["git_repository"]
    return bazelci.clone_git_repository(git_repository, platform_name)


def start_bisecting(project_name, platform_name, git_repo_location, commits_list):
    left = 0
    right = len(commits_list)
    while left < right:
        mid = (left + right) // 2
        mid_commit = commits_list[mid]
        bazelci.print_expanded_group(":bazel: Test with Bazel built at " + mid_commit)
        bazelci.eprint("Remaining suspected commits are:\n")
        for i in range(left, right):
            bazelci.eprint(commits_list[i] + "\n")
        if test_with_bazel_at_commit(project_name, platform_name, git_repo_location, mid_commit):
            bazelci.print_collapsed_group(":bazel: Succeeded at " + mid_commit)
            left = mid + 1
        else:
            bazelci.print_collapsed_group(":bazel: Failed at " + mid_commit)
            right = mid

    bazelci.print_expanded_group(":bazel: Bisect Result")
    if right == len(commits_list):
        bazelci.eprint("first bad commit not found, every commit succeeded.")
    else:
        first_bad_commit = commits_list[right]
        bazelci.eprint("first bad commit is " + first_bad_commit)
        os.chdir(BAZEL_REPO_DIR)
        bazelci.execute_command(["git", "--no-pager", "log", "-n", "1", first_bad_commit])


def print_culprit_finder_pipeline(project_name, platform_name, good_bazel_commit, bad_bazel_commit):
    host_platform = PLATFORMS[platform_name].get("host-platform", platform_name)
    pipeline_steps = []
    command = ("%s culprit_finder.py runner --project_name=\"%s\" --platform_name=%s --good_bazel_commit=%s --bad_bazel_commit=%s"
               % (bazelci.python_binary(platform_name), project_name, platform_name, good_bazel_commit, bad_bazel_commit))
    pipeline_steps.append({
            "label": PLATFORMS[platform_name]["emoji-name"] + " Bisecting for {0}".format(project_name),
            "command": [
                bazelci.fetch_bazelcipy_command(),
                fetch_culprit_finder_py_command(),
                command
            ],
            "agents": {
                "kind": "worker",
                "java": PLATFORMS[platform_name]["java"],
                "os": bazelci.rchop(host_platform, "_nojava", "_java8", "_java9", "_java10")
            }
        })
    print(yaml.dump({"steps": pipeline_steps}))


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Bazel Culprit Finder Script")

    subparsers = parser.add_subparsers(dest="subparsers_name")

    culprit_finder = subparsers.add_parser("culprit_finder")

    runner = subparsers.add_parser("runner")
    runner.add_argument("--project_name", type=str)
    runner.add_argument("--platform_name", type=str)
    runner.add_argument("--good_bazel_commit", type=str)
    runner.add_argument("--bad_bazel_commit", type=str)

    args = parser.parse_args(argv)
    try:
        if args.subparsers_name == "culprit_finder":
            try:
                project_name = os.environ["PROJECT_NAME"]
                platform_name = os.environ["PLATFORM_NAME"]
                good_bazel_commit = os.environ["GOOD_BAZEL_COMMIT"]
                bad_bazel_commit = os.environ["BAD_BAZEL_COMMIT"]
            except KeyError as e:
                raise BuildkiteException("Environment variable %s must be set" % str(e))

            if project_name not in DOWNSTREAM_PROJECTS:
                raise BuildkiteException("Project name '%s' not recognized, available projects are %s"
                                         % (project_name, str((DOWNSTREAM_PROJECTS.keys()))))

            if platform_name not in PLATFORMS:
                raise BuildkiteException("Platform name '%s' not recognized, available platforms are %s"
                                         % (platform_name, str((PLATFORMS.keys()))))
            print_culprit_finder_pipeline(project_name = project_name,
                                          platform_name = platform_name,
                                          good_bazel_commit = good_bazel_commit,
                                          bad_bazel_commit = bad_bazel_commit)
        elif args.subparsers_name == "runner":
            git_repo_location = clone_git_repository(args.project_name, args.platform_name)
            bazelci.print_collapsed_group("Check good bazel commit " + args.good_bazel_commit)
            if not test_with_bazel_at_commit(project_name = args.project_name,
                                             platform_name = args.platform_name,
                                             git_repo_location = git_repo_location,
                                             bazel_commit = args.good_bazel_commit):
                raise BuildkiteException("Given good commit (%s) is not actually good, abort bisecting."
                                         % args.good_bazel_commit)
            start_bisecting(project_name = args.project_name,
                            platform_name = args.platform_name,
                            git_repo_location = git_repo_location,
                            commits_list = get_bazel_commits_between(args.good_bazel_commit, args.bad_bazel_commit))
        else:
            parser.print_help()
            return 2

    except BuildkiteException as e:
        bazelci.eprint(str(e))
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
