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
# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring
# pylint: disable=unspecified-encoding
# pylint: disable=invalid-name
"""The CI script for Bazel Central Registry Presubmit."""


import argparse
import os
import pathlib
import re
import sys
import subprocess
import time
import yaml

import bazelci

BCR_REPO_DIR = pathlib.Path(os.getcwd())

BUILDKITE_ORG = os.environ["BUILDKITE_ORGANIZATION_SLUG"]

SCRIPT_URL = {
    "bazel-testing": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazel-central-registry/bcr_presubmit.py",
    "bazel-trusted": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazel-central-registry/bcr_presubmit.py",
    "bazel": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazel-central-registry/bcr_presubmit.py",
}[BUILDKITE_ORG] + "?{}".format(int(time.time()))


def fetch_bcr_presubmit_py_command():
    return "curl -s {0} -o bcr_presubmit.py".format(SCRIPT_URL)


class BcrPipelineException(Exception):
    """Raised whenever something goes wrong and we should exit with an error."""


def get_target_modules():
    """
    If the `MODULE_NAME` and `MODULE_VERSION(S)` are specified, calculate the target modules from those env vars.
    Otherwise, calculate target modules based on changed files from the main branch.
    """
    modules = []
    if "MODULE_NAME" in os.environ:
        name = os.environ["MODULE_NAME"]
        if "MODULE_VERSION" in os.environ:
            modules.append((name, os.environ["MODULE_VERSION"]))
        elif "MODULE_VERSIONS" in os.environ:
            for version in os.environ["MODULE_VERSIONS"].split(","):
                modules.append((name, version))

    if modules:
        return list(set(modules))

    # Get the list of changed files compared to the main branch
    output = subprocess.check_output(
        ["git", "diff", "main", "--name-only", "--pretty=format:"]
    )
    # Matching modules/<name>/<version>/
    for line in output.decode("utf-8").split():
        s = re.match(r"modules\/([^\/]+)\/([^\/]+)\/", line)
        if s:
            modules.append(s.groups())

    return list(set(modules))


def get_presubmit_yml(module_name, module_version):
    return BCR_REPO_DIR.joinpath("modules/%s/%s/presubmit.yml" % (module_name, module_version))


def get_task_config(module_name, module_version):
    return bazelci.load_config(http_url=None,
                               file_config=get_presubmit_yml(module_name, module_version),
                               allow_imports=False)


def add_presubmit_jobs(module_name, module_version, task_config, pipeline_steps):
    for task_name in task_config:
        platform_name = bazelci.get_platform_for_task(task_name, task_config)
        label = bazelci.PLATFORMS[platform_name]["emoji-name"] + " {0}@{1}".format(
            module_name, module_version
        )
        command = (
            '%s bcr_presubmit.py runner --module_name="%s" --module_version="%s" --task=%s'
            % (
                bazelci.PLATFORMS[platform_name]["python"],
                module_name,
                module_version,
                task_name,
            )
        )
        commands = [bazelci.fetch_bazelcipy_command(), fetch_bcr_presubmit_py_command(), command]
        pipeline_steps.append(bazelci.create_step(label, commands, platform_name))


def scratch_file(root, relative_path, lines=None):
    """Creates a file under the root directory"""
    if not relative_path:
        return None
    abspath = pathlib.Path(root).joinpath(relative_path)
    with open(abspath, 'w') as f:
        if lines:
            for l in lines:
                f.write(l)
                f.write('\n')
    return abspath


def create_test_repo(module_name, module_version, task):
    configs = get_task_config(module_name, module_version)
    platform = bazelci.get_platform_for_task(task, configs.get("tasks", None))
    # TODO(pcloudy): We use the "downstream root" as the repo root, find a better root path for BCR presubmit.
    root = pathlib.Path(bazelci.downstream_projects_root(platform))
    scratch_file(root, "WORKSPACE")
    scratch_file(root, "BUILD")
    # TODO(pcloudy): Should we test this module as the root module? Maybe we do if we support dev dependency.
    # Because if the module is not root module, dev dependencies are ignored, which can break test targets.
    # Another work around is that we can copy the dev dependencies to the generated MODULE.bazel.
    scratch_file(root, "MODULE.bazel", ["bazel_dep(name = '%s', version = '%s')" % (module_name, module_version)])
    scratch_file(root, ".bazelrc", [
        "build --experimental_enable_bzlmod",
        "build --registry=%s" % BCR_REPO_DIR.as_uri(),
    ])
    return root


def run_test(repo_location, module_name, module_version, task):
    try:
        return bazelci.main(
            [
                "runner",
                "--task=" + task,
                "--file_config=%s" % get_presubmit_yml(module_name, module_version),
                "--repo_location=%s" % repo_location,
            ]
        )
    except subprocess.CalledProcessError as e:
        bazelci.eprint(str(e))
        return 1


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Bazel Central Regsitry Presubmit Test Generator")

    subparsers = parser.add_subparsers(dest="subparsers_name")

    subparsers.add_parser("bcr_presubmit")

    runner = subparsers.add_parser("runner")
    runner.add_argument("--module_name", type=str)
    runner.add_argument("--module_version", type=str)
    runner.add_argument("--task", type=str)

    args = parser.parse_args(argv)
    if args.subparsers_name == "bcr_presubmit":
        modules = get_target_modules()
        if not modules:
            bazelci.eprint("No target modules detected in this branch!")
        pipeline_steps = []
        for module_name, module_version in modules:
            configs = get_task_config(module_name, module_version)
            add_presubmit_jobs(module_name, module_version, configs.get("tasks", None), pipeline_steps)
        print(yaml.dump({"steps": pipeline_steps}))
    elif args.subparsers_name == "runner":
        repo_location = create_test_repo(args.module_name, args.module_version, args.task)
        return run_test(repo_location, args.module_name, args.module_version, args.task)
    else:
        parser.print_help()
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
