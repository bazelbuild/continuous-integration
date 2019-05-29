#!/usr/bin/env python3
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
import shutil
import subprocess
import sys
import tempfile
import yaml


def _platform_path_str(posix_path):
  """Converts the path to the appropriate format for platform."""
  if os.name == "nt":
    return posix_path.replace("/", "\\")
  return posix_path


# TODO(leba): Make these configurable via flags to the script.
# TMP has different values, depending on the platform.
TMP = tempfile.gettempdir()
# The path to the directory that stores the bazel binaries.
BAZEL_BINARY_BASE_PATH = _platform_path_str("%s/.bazel-bench/bazel-bin/" % TMP)
PROJECTS = [
    {
        "name": "Bazel",
        "git_repository": "https://github.com/bazelbuild/bazel.git",
        "bazel_command": "build ..."
    }
]
BAZEL_REPOSITORY = "https://github.com/bazelbuild/bazel.git"
DATA_DIRECTORY = _platform_path_str("%s/.bazel-bench/out/" % TMP)
RUNS = 3


def get_bazel_commits(day):
  """Get the commits from a particular day.

  Get the commits from 00:00 of day to 00:00 of day + 1.

  Args:
    day: a datetime.date the day to get commits.

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
      "--reverse"
  ]
  command = subprocess.Popen(args, stdout=subprocess.PIPE)
  return [
      line.decode("utf-8").rstrip("\n").strip("'") for line in command.stdout]


def get_platforms(project_name):
    """Get the platforms on which this project is run on BazelCI.

    Args:
      project_name: a string: the name of the project. e.g. "Bazel".

    Returns:
      A list of string: the platforms for this project.
    """
    http_config = bazelci.DOWNSTREAM_PROJECTS[project_name]["http_config"]
    configs = bazelci.fetch_configs(http_config, None)
    tasks = configs["tasks"]
    return list(map(lambda k: bazelci.get_platform_for_task(k, tasks), tasks))


def ci_step_for_platform_and_commits(
    bazel_commits, platform, project, extra_options):
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
  # Download the binaries already built.
  # Bazel-bench won"t try to build these binaries again, since they exist.
  for bazel_commit in bazel_commits:
    bazelci.download_bazel_binary_at_commit(
        BAZEL_BINARY_BASE_PATH + bazel_commit,
        platform,
        bazel_commit
    )
  project_mirror_path = bazelci.get_mirror_path(
      project["git_repository"], platform)
  bazel_mirror_path = bazelci.get_mirror_path(BAZEL_REPOSITORY, platform)

  args = [
      "bazel",
      "run",
      "benchmark",
      "--",
      "--bazel_commits=%s" % ",".join(commits),
      "--bazel_source=%s" % bazel_mirror_path,
      "--project_source=%s" % project_mirror_path,
      "--collect_memory",
      "--runs=%s" % RUNS,
      "--data_directory=%s" % DATA_DIRECTORY,
      extra_options,
      "--",
      project["bazel_command"]
  ]

  label = (bazelci.PLATFORMS[platform]["emoji-name"]
           + " Running bazel-bench on project: %s" % project["name"])
  return bazelci.create_step(label, " ".join(args), platform)


def main(args=None):
  if agrs is None:
    args = sys.argv[1:]

  parser = argparse.ArgumentParser(description="Bazel Bench CI Pipeline")
  parser.add_argument("--day", type=str)
  parser.add_argument("--bazel_bench_options", type=str, default="")
  parsed_args = parser.parse_args(args)

  bazel_bench_ci_steps = []
  day = (
      datetime.datetime.strptime(parsed_args.day, "%Y-%m-%d").date()
      if parsed_args.day
      else datetime.date.today())
  bazel_commits = get_bazel_commits(day)
  for project in PROJECTS:
    for platform in get_platforms(project["name"]):
      # bazel-bench doesn't support Windows for now.
      if platform == "windows":
        continue
      bazel_bench_ci_steps.append(
          ci_step_for_platform_and_commits(
              bazel_commits,
              platform,
              project,
              parsed_args.bazel_bench_options))

  # Print the commands
  print(yaml.dump({"steps": bazel_bench_ci_steps}))

if __name__ == "__main__":
  sys.exit(main())

