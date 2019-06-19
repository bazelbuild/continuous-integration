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
import json
import os
import subprocess
import sys
import tempfile
import time
import yaml


# TMP has different values, depending on the platform.
TMP = tempfile.gettempdir()
PROJECTS = [
    {
        "name": "Bazel",
        "storage_subdir": "bazel",
        "git_repository": "https://github.com/bazelbuild/bazel.git",
        "bazel_command": "build //src:bazel-bin",
    }
]
BAZEL_REPOSITORY = "https://github.com/bazelbuild/bazel.git"
DATA_DIRECTORY = os.path.join(TMP, ".bazel-bench", "out")
BAZEL_BENCH_RESULT_FILENAME = "perf_data.csv"
JSON_PROFILES_AGGR_FILENAME = "json_profiles_aggr.csv"


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


def _get_bazel_commits(date, bazel_repo_path):
    """Get the commits from a particular date.

    Get the commits from 00:00 of date to 00:00 of date + 1.

    Args:
      date: a datetime.date the date to get commits.
      bazel_repo_path: the path to a local clone of bazelbuild/bazel.

    Return:
      A list of string (commit hashes).
    """
    date_plus_one = date + datetime.timedelta(days=1)
    args = [
        "git",
        "log",
        "--pretty=format:'%H'",
        "--after='%s'" % date.strftime("%Y-%m-%d 00:00"),
        "--until='%s'" % date_plus_one.strftime("%Y-%m-%d 00:00"),
        "--reverse",
    ]
    command_output = subprocess.check_output(args, cwd=bazel_repo_path)
    decoded = command_output.decode("utf-8").split("\n")

    return [line.strip("'") for line in decoded]


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


def _ci_step_for_platform_and_commits(bazel_commits, platform, project, extra_options, date):
    """Perform bazel-bench for the platform-project combination.
    Uploads results to BigQuery.

    Args:
        bazel_commits: a list of strings: bazel commits to be benchmarked.
        platform: a string: the platform to benchmark on.
        project: an object: contains the information of the project to be
          tested on.
        extra_options: a string: extra bazel-bench options.
        date: the date of the commits.

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
            "--csv_file_name=%s" % BAZEL_BENCH_RESULT_FILENAME,
            "--collect_json_profile",
            "--aggregate_json_profiles",
            extra_options,
            "--",
            project["bazel_command"],
        ]
    )

    # Upload the raw data in the csv file to BigQuery.
    upload_result_bq_command = " ".join(
        [
            "bazel",
            "run",
            "//utils:bigquery_upload",
            "--",
            "-upload_to_bigquery=blaze-perf:bazel_playground:bazel_bench:europe-west2",
            "--",
            "{}/{}".format(DATA_DIRECTORY, BAZEL_BENCH_RESULT_FILENAME),
        ]
    )

    # Upload the aggregated JSON profile to BigQuery.
    upload_json_prof_aggr_bq_command = " ".join(
        [
            "bazel",
            "run",
            "//utils:bigquery_upload",
            "--",
            "-upload_to_bigquery=blaze-perf:bazel_playground:json_profiles_aggr:europe-west2",
            "--",
            "{}/{}".format(DATA_DIRECTORY, JSON_PROFILES_AGGR_FILENAME),
        ]
    )

    # Upload everything under DATA_DIRECTORY to Storage.
    # This includes the raw data, aggr JSON profile and the JSON profiles
    # themselves.
    storage_subdir = "{}/{}/{}/".format(
        project["storage_subdir"], date.strftime("%Y/%m/%d"), platform
    )
    upload_output_files_storage_command = " ".join(
        [
            "bazel",
            "run",
            "//utils:storage_upload",
            "--",
            "-upload_to_storage=blaze-perf:bazel-bench:{}".format(storage_subdir),
            "--",
            "{}/*".format(DATA_DIRECTORY),
        ]
    )
    commands = (
        [bazelci.fetch_bazelcipy_command()]
        + _bazel_bench_env_setup_command(platform, ",".join(bazel_commits))
        + [
            bazel_bench_command,
            upload_result_bq_command,
            upload_json_prof_aggr_bq_command,
            upload_output_files_storage_command,
        ]
    )
    label = (
        bazelci.PLATFORMS[platform]["emoji-name"]
        + " Running bazel-bench on project: %s" % project["name"]
    )
    return bazelci.create_step(label, commands, platform)


def _metadata_file_content(project_label, command, date, platforms):
    """Generate the METADATA file for each project.

    Args:
        project_label: the label of the project on Storage.
        command: the bazel command executed during the runs e.g. bazel build ...
        date: the date of the runs.
        platform: the platform the runs were performed on.
    Returns:
        The content of the METADATA file for the project on that date.
    """
    data_root = "https://bazel-bench.storage.googleapis.com/{}/{}".format(
        project_label, date.strftime("%Y/%m/%d")
    )

    return {
        "name": project_label,
        "command": command,
        "data_root": data_root,
        "platforms": [
            {
                "platform": platform,
                "perf_data": "{}/{}".format(platform, BAZEL_BENCH_RESULT_FILENAME),
                "json_profiles_aggr": "{}/{}".format(platform, JSON_PROFILES_AGGR_FILENAME),
            }
            for platform in platforms
        ],
    }


def _create_and_upload_metadata(project_label, command, date, platforms):
    """Generate the METADATA file for each project & upload to Storage.

    METADATA provides information about the runs and where to get the
    measurements. It is later used by the script that generates the daily report
    to construct the graphs.

    Args:
        project_label: the label of the project on Storage.
        command: the bazel command executed during the runs e.g. bazel build ...
        date: the date of the runs.
        platform: the platform the runs were performed on.
    """
    metadata_file_path = "{}/{}-metadata".format(TMP, project_label)

    with open(metadata_file_path, "w") as f:
        data = _metadata_file_content(project_label, command, date, platforms)
        json.dump(data, f)

    destination = "gs://bazel-bench/{}/{}/METADATA".format(project_label, date.strftime("%Y/%m/%d"))
    args = ["gsutil", "cp", metadata_file_path, destination]

    try:
        subprocess.check_output(args)
        bazelci.eprint("Uploaded {}'s METADATA to {}.".format(project_label, destination))
    except subprocess.CalledProcessError as e:
        bazelci.eprint("Error uploading: {}".format(e))


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Bazel Bench CI Pipeline")
    parser.add_argument("--date", type=str)
    parser.add_argument("--bazel_bench_options", type=str, default="")
    parsed_args = parser.parse_args(args)

    bazel_bench_ci_steps = []
    date = (
        datetime.datetime.strptime(parsed_args.date, "%Y-%m-%d").date()
        if parsed_args.date
        else datetime.date.today()
    )
    bazel_commits = None

    for project in PROJECTS:
        platforms = _get_platforms(project["name"])
        for platform in platforms:
            # bazel-bench doesn't support Windows for now.
            if platform in ["windows"]:
                continue

            # When running on the first platform, get the bazel commits.
            # The bazel commits should be the same regardless of platform.
            if not bazel_commits:
                bazel_clone_path = bazelci.clone_git_repository(BAZEL_REPOSITORY, platform)
                bazel_commits = _get_bazel_commits(date, bazel_clone_path)

            bazel_bench_ci_steps.append(
                _ci_step_for_platform_and_commits(
                    bazel_commits, platform, project, parsed_args.bazel_bench_options, date
                )
            )
        _create_and_upload_metadata(
            project_label=project["storage_subdir"],
            command=project["bazel_command"],
            date=date,
            platforms=platforms,
        )

    bazelci.eprint(yaml.dump({"steps": bazel_bench_ci_steps}))
    buildkite_pipeline_cmd = "cat <<EOF | buildkite-agent pipeline upload\n%s\nEOF" % yaml.dump(
        {"steps": bazel_bench_ci_steps}
    )
    subprocess.call(buildkite_pipeline_cmd, shell=True)


if __name__ == "__main__":
    sys.exit(main())
