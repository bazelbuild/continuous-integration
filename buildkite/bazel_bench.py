#!/usr/bin/env python3
#
# Copyright 2019 The Bazel Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
This script is downloaded and executed by BuildKite when the pipeline starts.
Runs bazel-bench on the defined projects, on every platforms the project runs
on.
"""

import argparse
import bazelci
import datetime
import os
import subprocess
import sys
import tempfile
import time
import yaml


def _platform_path_str(posix_path):
    """Converts the path to the appropriate format for platform."""
    if os.name == "nt":
        return posix_path.replace("/", "\\")
    return posix_path


# TMP has different values, depending on the platform.
TMP = tempfile.gettempdir()
PROJECTS = [
    {
        "name": "Bazel",
        "git_repository": "https://github.com/bazelbuild/bazel.git",
        "bazel_command": "build ...",
    }
]
BAZEL_REPOSITORY = "https://github.com/bazelbuild/bazel.git"
DATA_DIRECTORY = _platform_path_str("%s/.bazel-bench/out/" % TMP)


def _bazel_bench_env_setup_command(platform, bazel_commits):
    bazel_bench_env_setup_py_url = (
        "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazel_bench_env_setup.py?%s"
        % int(time.time())
    )
    download_command = 'curl -sS "%s" -o bazel_bench_env_setup.py' % bazel_bench_env_setup_py_url
    exec_command = "%s bazel_bench_env_setup.py --platform=%s --bazel_commits=%s" % (
        bazelci.PLATFORMS[platform]["python"],
        platform,
        bazel_commits,
    )
    return [download_command, exec_command]


def _get_bazel_commits(day, bazel_repo_path):
    """Get the commits from a particular day.

  Get the commits from 00:00 of day to 00:00 of day + 1.

  Args:
    day: a datetime.date the day to get commits.
    bazel_repo_path: the path to a local clone of bazelbuild/bazel.

  Return:
    A list of string (commit hashes).
  """
    day_plus_one = day + datetime.timedelta(days=1)
    args = [
        "git",
        "log",
        "--pretty=format:'%H'",
        "--after='%s'" % day.strftime("%Y-%m-%d 00:00"),
        "--until='%s'" % day_plus_one.strftime("%Y-%m-%d 00:00"),
        "--reverse",
    ]
    command_output = subprocess.check_output(args, cwd=bazel_repo_path)
    return [line.decode("utf-8").rstrip("\n").strip("'") for line in command_output]


def _get_platforms(project_name):
    """Get the platforms on which this project is run on BazelCI.

  Args:
    project_name: a string: the name of the project. e.g. "Bazel".

  Returns:
    A list of string: the platforms for this project.
  """
    http_config = bazelci.DOWNSTREAM_PROJECTS_PRODUCTION[project_name]["http_config"]
    configs = bazelci.fetch_configs(http_config, None)
    tasks = configs["tasks"]
    return list(map(lambda k: bazelci.get_platform_for_task(k, tasks[k]), tasks))


def _get_clone_path(repository, platform):
    """Returns the path to a local clone of the project.

  If there's a mirror available, use that. bazel-bench will take care of
  pulling/checking out commits. Else, clone the repo.

  Args:
    repository: the URL to the git repository.
    platform: the platform on which to build the project.

  Returns:
    A path to the local clone.
  """
    mirror_path = bazelci.get_mirror_path(repository, platform)
    if os.path.exists(mirror_path):
        bazelci.eprint("Found mirror for %s on %s." % repository, platform)
        return mirror_path

    return repository


def _ci_step_for_platform_and_commits(bazel_commits, platform, project, extra_options):
    """Perform bazel-bench for the platform-project combination.
  Uploads results to BigQuery.

  Args:
    bazel_commits: a list of strings: bazel commits to be benchmarked.
    platform: a string: the platform to benchmark on.
    project: an object: contains the information of the project to be
      tested on.
    extra_options: a string: extra bazel-bench options.

  Return:
    An object: the result of applying bazelci.create_step to wrap the
      command to be executed by buildkite-agent.
  """
    project_clone_path = _get_clone_path(project["git_repository"], platform)
    bazel_clone_path = _get_clone_path(BAZEL_REPOSITORY, platform)

    bazel_bench_command = " ".join(
        [
            "bazel",
            "run",
            "benchmark",
            "--",
            "--bazel_commits=%s" % ",".join(bazel_commits),
            "--bazel_source=%s" % bazel_clone_path,
            "--project_source=%s" % project_clone_path,
            "--platform=%s" % platform,
            "--collect_memory",
            "--data_directory=%s" % DATA_DIRECTORY,
            extra_options,
            "--",
            project["bazel_command"],
        ]
    )

    commands = (
        [bazelci.fetch_bazelcipy_command()]
        + _bazel_bench_env_setup_command(platform, ",".join(bazel_commits))
        + [bazel_bench_command]
    )
    label = (
        bazelci.PLATFORMS[platform]["emoji-name"]
        + " Running bazel-bench on project: %s" % project["name"]
    )
    return bazelci.create_step(label, commands, platform)


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Bazel Bench CI Pipeline")
    parser.add_argument("--day", type=str)
    parser.add_argument("--bazel_bench_options", type=str, default="")
    parsed_args = parser.parse_args(args)

    bazel_bench_ci_steps = []
    day = (
        datetime.datetime.strptime(parsed_args.day, "%Y-%m-%d").date()
        if parsed_args.day
        else datetime.date.today()
    )
    bazel_commits = None
    for project in PROJECTS:
        for platform in _get_platforms(project["name"]):
            # bazel-bench doesn't support Windows for now.
            if platform in ["windows"]:
                continue

            # When running on the first platform, get the bazel commits.
            # The bazel commits should be the same regardless of platform.
            if not bazel_commits:
                bazel_clone_path = bazelci.clone_git_repository(BAZEL_REPOSITORY, platform)
                bazel_commits = _get_bazel_commits(day, bazel_clone_path)

            bazel_bench_ci_steps.append(
                _ci_step_for_platform_and_commits(
                    bazel_commits, platform, project, parsed_args.bazel_bench_options
                )
            )

    bazelci.eprint(yaml.dump({"steps": bazel_bench_ci_steps}))
    buildkite_pipeline_cmd = "cat <<EOF | buildkite-agent pipeline upload\n%s\nEOF" % yaml.dump(
        {"steps": bazel_bench_ci_steps}
    )
    subprocess.call(buildkite_pipeline_cmd, shell=True)


if __name__ == "__main__":
    sys.exit(main())
