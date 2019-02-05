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
import codecs
import random
import sys
import urllib.request
import yaml

from config import PLATFORMS
import print_project_pipeline
import update_last_green_commit
import print_bazel_publish_binaries_pipeline
import print_bazel_downstream_pipeline
import publish_binaries

# Initialize the random number generator.
random.seed()

# The platform used for various steps (e.g. stuff that formerly ran on the "pipeline" workers).
DEFAULT_PLATFORM = "ubuntu1804"


def fetch_configs(http_url, file_config):
    """
    If specified fetches the build configuration from file_config or http_url, else tries to
    read it from .bazelci/presubmit.yml.
    Returns the json configuration as a python data structure.
    """
    if file_config is not None and http_url is not None:
        raise Exception("file_config and http_url cannot be set at the same time")

    if file_config is not None:
        with open(file_config, "r") as fd:
            return yaml.load(fd)
    if http_url is not None:
        with urllib.request.urlopen(http_url) as resp:
            reader = codecs.getreader("utf-8")
            return yaml.load(reader(resp))
    with open(".bazelci/presubmit.yml", "r") as fd:
        return yaml.load(fd)


# This is so that multiline python strings are represented as YAML
# block strings.
def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    yaml.add_representer(str, str_presenter)

    parser = argparse.ArgumentParser(description="Bazel Continuous Integration Script")

    subparsers = parser.add_subparsers(dest="subparsers_name")

    bazel_publish_binaries_pipeline = subparsers.add_parser("bazel_publish_binaries_pipeline")
    bazel_publish_binaries_pipeline.add_argument("--file_config", type=str)
    bazel_publish_binaries_pipeline.add_argument("--http_config", type=str)
    bazel_publish_binaries_pipeline.add_argument("--git_repository", type=str)

    bazel_downstream_pipeline = subparsers.add_parser("bazel_downstream_pipeline")
    bazel_downstream_pipeline.add_argument("--file_config", type=str)
    bazel_downstream_pipeline.add_argument("--http_config", type=str)
    bazel_downstream_pipeline.add_argument("--git_repository", type=str)
    bazel_downstream_pipeline.add_argument(
        "--test_incompatible_flags", type=bool, nargs="?", const=True
    )
    bazel_downstream_pipeline.add_argument(
        "--test_disabled_projects", type=bool, nargs="?", const=True
    )

    project_pipeline = subparsers.add_parser("project_pipeline")
    project_pipeline.add_argument("--project_name", type=str)
    project_pipeline.add_argument("--file_config", type=str)
    project_pipeline.add_argument("--http_config", type=str)
    project_pipeline.add_argument("--git_repository", type=str)
    project_pipeline.add_argument("--monitor_flaky_tests", type=bool, nargs="?", const=True)
    project_pipeline.add_argument("--use_but", type=bool, nargs="?", const=True)
    project_pipeline.add_argument("--incompatible_flag", type=str, action="append")

    runner = subparsers.add_parser("runner")
    runner.add_argument("--platform", action="store", choices=list(PLATFORMS))
    runner.add_argument("--file_config", type=str)
    runner.add_argument("--http_config", type=str)
    runner.add_argument("--git_repository", type=str)
    runner.add_argument(
        "--git_commit", type=str, help="Reset the git repository to this commit after cloning it"
    )
    runner.add_argument(
        "--git_repo_location",
        type=str,
        help="Use an existing repository instead of cloning from github",
    )
    runner.add_argument(
        "--use_bazel_at_commit", type=str, help="Use Bazel binary built at a specific commit"
    )
    runner.add_argument("--use_but", type=bool, nargs="?", const=True)
    runner.add_argument("--save_but", type=bool, nargs="?", const=True)
    runner.add_argument("--needs_clean", type=bool, nargs="?", const=True)
    runner.add_argument("--build_only", type=bool, nargs="?", const=True)
    runner.add_argument("--test_only", type=bool, nargs="?", const=True)
    runner.add_argument("--monitor_flaky_tests", type=bool, nargs="?", const=True)
    runner.add_argument("--incompatible_flag", type=str, action="append")

    runner = subparsers.add_parser("publish_binaries")

    runner = subparsers.add_parser("try_update_last_green_commit")

    args = parser.parse_args(argv)

    if args.subparsers_name == "bazel_publish_binaries_pipeline":
        configs = fetch_configs(args.http_config, args.file_config)
        print_bazel_publish_binaries_pipeline.main(
            configs=configs.get("platforms", None),
            http_config=args.http_config,
            file_config=args.file_config,
        )
    elif args.subparsers_name == "bazel_downstream_pipeline":
        configs = fetch_configs(args.http_config, args.file_config)
        print_bazel_downstream_pipeline.main(
            configs=configs.get("platforms", None),
            http_config=args.http_config,
            file_config=args.file_config,
            test_incompatible_flags=args.test_incompatible_flags,
            test_disabled_projects=args.test_disabled_projects,
        )
    elif args.subparsers_name == "project_pipeline":
        configs = fetch_configs(args.http_config, args.file_config)
        print_project_pipeline.main(
            configs=configs,
            project_name=args.project_name,
            http_config=args.http_config,
            file_config=args.file_config,
            git_repository=args.git_repository,
            monitor_flaky_tests=args.monitor_flaky_tests,
            use_but=args.use_but,
            incompatible_flags=args.incompatible_flag,
        )
    elif args.subparsers_name == "runner":
        configs = fetch_configs(args.http_config, args.file_config)
        runner.main(
            config=configs.get("platforms", None)[args.platform],
            platform=args.platform,
            git_repository=args.git_repository,
            git_commit=args.git_commit,
            git_repo_location=args.git_repo_location,
            use_bazel_at_commit=args.use_bazel_at_commit,
            use_but=args.use_but,
            save_but=args.save_but,
            needs_clean=args.needs_clean,
            build_only=args.build_only,
            test_only=args.test_only,
            monitor_flaky_tests=args.monitor_flaky_tests,
            incompatible_flags=args.incompatible_flag,
        )
    elif args.subparsers_name == "publish_binaries":
        publish_binaries.main()
    elif args.subparsers_name == "try_update_last_green_commit":
        update_last_green_commit.main()
    else:
        parser.print_help()
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
