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
import json
import os
import pathlib
import re
import sys
import subprocess
import shutil
import time
import urllib.request
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


def error(msg):
    bazelci.eprint("\x1b[31mERROR\x1b[0m: {}\n".format(msg))
    raise BcrPipelineException("BCR Presubmit failed!")


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
        ["git", "diff", "main...HEAD", "--name-only", "--pretty=format:"]
    )
    # Matching modules/<name>/<version>/
    for line in output.decode("utf-8").split():
        s = re.match(r"modules\/([^\/]+)\/([^\/]+)\/", line)
        if s:
            modules.append(s.groups())

    return list(set(modules))


def get_presubmit_yml(module_name, module_version):
    return BCR_REPO_DIR.joinpath("modules/%s/%s/presubmit.yml" % (module_name, module_version))


def get_module_dot_bazel(module_name, module_version):
    return BCR_REPO_DIR.joinpath("modules/%s/%s/MODULE.bazel" % (module_name, module_version))


def get_source_json(module_name, module_version):
    return BCR_REPO_DIR.joinpath("modules/%s/%s/source.json" % (module_name, module_version))


def get_patch_file(module_name, module_version, patch):
    return BCR_REPO_DIR.joinpath("modules/%s/%s/patches/%s" % (module_name, module_version, patch))


def get_task_config(module_name, module_version):
    return bazelci.load_config(http_url=None,
                               file_config=get_presubmit_yml(module_name, module_version),
                               allow_imports=False)


def get_test_module_task_config(module_name, module_version):
    orig_presubmit = yaml.safe_load(open(get_presubmit_yml(module_name, module_version), "r"))
    if "bcr_test_module" in orig_presubmit:
        config = orig_presubmit["bcr_test_module"]
        bazelci.expand_task_config(config)
        return config
    return {}


def add_presubmit_jobs(module_name, module_version, task_configs, pipeline_steps, is_test_module=False):
    for task_name, task_config in task_configs.items():
        platform_name = bazelci.get_platform_for_task(task_name, task_config)
        label = bazelci.PLATFORMS[platform_name]["emoji-name"] + " {0}@{1} {2}".format(
            module_name, module_version, task_config["name"] if "name" in task_config else ""
        )
        command = (
            '%s bcr_presubmit.py %s --module_name="%s" --module_version="%s" --task=%s'
            % (
                bazelci.PLATFORMS[platform_name]["python"],
                "test_module_runner" if is_test_module else "runner",
                module_name,
                module_version,
                task_name,
            )
        )
        commands = [bazelci.fetch_bazelcipy_command(), fetch_bcr_presubmit_py_command(), command]
        pipeline_steps.append(bazelci.create_step(label, commands, platform_name))


def scratch_file(root, relative_path, lines=None, mode="w"):
    """Creates a file under the root directory"""
    if not relative_path:
        return None
    abspath = pathlib.Path(root).joinpath(relative_path)
    with open(abspath, mode) as f:
        if lines:
            for l in lines:
                f.write(l)
                f.write('\n')
    return abspath


def get_root_dir(module_name, module_version, task, is_test_module=False):
    # TODO(pcloudy): We use the "downstream root" as the repo root, find a better root path for BCR presubmit.
    configs = get_test_module_task_config(module_name, module_version) if is_test_module else get_task_config(module_name, module_version)
    platform = bazelci.get_platform_for_task(task, configs["tasks"][task])
    return pathlib.Path(bazelci.downstream_projects_root(platform))


def create_simple_repo(module_name, module_version, task):
    """Create a simple Bazel module repo which depends on the target module."""
    root = get_root_dir(module_name, module_version, task)
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


def download(url, file):
    with urllib.request.urlopen(url) as response:
        with open(file, "wb") as f:
            f.write(response.read())


def read(path):
    with open(path, "r") as file:
        return file.read()


def load_source_json(module_name, module_version):
    source_json = get_source_json(module_name, module_version)
    with open(source_json, "r") as json_file:
        return json.load(json_file)


def apply_patch(work_dir, patch_strip, patch_file):
    # Requires `patch` to be installed, this is true for all Bazel CI VMs, including Windows VMs.
    subprocess.run(
        ["patch", "-p%d" % patch_strip, "-i", patch_file], shell=False, check=True, env=os.environ, cwd=work_dir
    )


def prepare_test_module_repo(module_name, module_version, task):
    """Prepare the test module repo and the presubmit yml file it should use"""
    bazelci.print_collapsed_group(":information_source: Prepare test module repo")
    root = get_root_dir(module_name, module_version, task, is_test_module = True)
    source = load_source_json(module_name, module_version)

    # Download and unpack the source archive to ./output
    archive_url = source["url"]
    archive_file = root.joinpath(archive_url.split("/")[-1])
    output_dir = root.joinpath("output")
    bazelci.eprint("* Download and unpack %s\n" % archive_url)
    download(archive_url, archive_file)
    shutil.unpack_archive(str(archive_file), output_dir)
    bazelci.eprint("Source unpacked to %s\n" % output_dir)

    # Apply patch files if there are any
    source_root = output_dir.joinpath(source["strip_prefix"] if "strip_prefix" in source else "")
    if "patches" in source:
        bazelci.eprint("* Applying patch files")
        for patch_name in source["patches"]:
            bazelci.eprint("\nApplying %s:" % patch_name)
            patch_file = get_patch_file(module_name, module_version, patch_name)
            apply_patch(source_root, source["patch_strip"], patch_file)

    # Make sure the checked-in MODULE.bazel file is used.
    checked_in_module_dot_bazel = get_module_dot_bazel(module_name, module_version)
    bazelci.eprint("\n* Copy checked-in MODULE.bazel file to source root:\n%s\n" % read(checked_in_module_dot_bazel))
    shutil.copy(checked_in_module_dot_bazel, source_root.joinpath("MODULE.bazel"))

    # Generate the presubmit.yml file for the test module, it should be the content under "bcr_test_module"
    orig_presubmit = yaml.safe_load(open(get_presubmit_yml(module_name, module_version), "r"))
    test_module_presubmit = root.joinpath("presubmit.yml")
    with open(test_module_presubmit, "w") as f:
        yaml.dump(orig_presubmit["bcr_test_module"], f)
    bazelci.eprint("* Generate test module presubmit.yml:\n%s\n" % read(test_module_presubmit))

    # Write necessary options to the .bazelrc file
    test_module_root = source_root.joinpath(orig_presubmit["bcr_test_module"]["module_path"])
    scratch_file(test_module_root, ".bazelrc", [
        "build --experimental_enable_bzlmod",
        "build --registry=%s" % BCR_REPO_DIR.as_uri(),
    ], mode="a")
    bazelci.eprint("* Append Bzlmod flags to .bazelrc file:\n%s\n" % read(test_module_root.joinpath(".bazelrc")))

    bazelci.eprint("* Test module ready: %s\n" % test_module_root)
    return test_module_root, test_module_presubmit


def run_test(repo_location, task_config_file, task):
    try:
        return bazelci.main(
            [
                "runner",
                "--task=" + task,
                "--file_config=%s" % task_config_file,
                "--repo_location=%s" % repo_location,
            ]
        )
    except subprocess.CalledProcessError as e:
        bazelci.eprint(str(e))
        return 1


def validate_existing_modules_are_not_modified():
    # Get all files that are Modified, Renamed, or Deleted.
    bazelci.print_expanded_group("Checking if existing modules are not modified")
    output = subprocess.check_output(
        ["git", "diff", "main...HEAD", "--diff-filter=MRD", "--name-only", "--pretty=format:"]
    )

    # Check if any of the source.json, MODULE.bazel, or patch files are changed for an existing module.
    NO_CHANGE_FILE_PATTERNS = [
        re.compile(r"modules\/([^\/]+)\/([^\/]+)\/source.json"),
        re.compile(r"modules\/([^\/]+)\/([^\/]+)\/MODULE.bazel"),
        re.compile(r"modules\/([^\/]+)\/([^\/]+)\/patches"),
    ]
    changed_modules = []
    for line in output.decode("utf-8").split():
        for p in NO_CHANGE_FILE_PATTERNS:
            s = p.match(line)
            if s:
                bazelci.eprint(line, "was changed")
                changed_modules.append(s.groups())
    if changed_modules:
        error("Existing modules should not be changed:\n" + "\n".join([f"{name}@{version}" for name,version in changed_modules]))
    else:
        bazelci.eprint("No existing module was changed.")


def validate_files_outside_of_modules_dir_are_not_modified(modules):
    # If no modules are changed at the same time, then we don't need to perform this check.
    if not modules:
        return
    bazelci.print_expanded_group("Checking if any file changes outside of modules/")
    output = subprocess.check_output(
        ["git", "diff", "main...HEAD", "--name-only", "--pretty=format:", ":!modules"]
    ).decode("utf-8").strip()
    if output:
        error("The following files should not be changed when adding a new module version:\n" + output)
    else:
        bazelci.eprint("Nothing changed outside of modules/")


def should_bcr_validation_block_presubmit(modules):
    bazelci.print_collapsed_group("Running BCR validations:")
    returncode = subprocess.run(
        ["python3", "./tools/bcr_validation.py", "--check_all_metadata"] + [f"--check={name}@{version}" for name, version in modules]
    ).returncode
    # When a BCR maintainer view is required, the script should return 42.
    if returncode == 42:
        return True
    if returncode != 0:
        raise BcrPipelineException("BCR validation failed!")
    return False


def should_wait_bcr_maintainer_review(modules):
    """Validate the changes and decide whether the presubmit should wait for a BCR maintainer review.
    Returns False if all changes look good and the presubmit can proceed.
    Returns True if the changes should block follow up presubmit jobs until a BCR maintainer triggers them.
    Throws an error if the changes violate BCR policies or the BCR validations fail.
    """
    # If existing modules are changed, fail the presubmit.
    validate_existing_modules_are_not_modified()

    # If files outside of the modules/ directory are changed, fail the presubmit.
    validate_files_outside_of_modules_dir_are_not_modified(modules)

    # Run BCR validations on target modules and decide if the presubmit jobs should be blocked.
    return should_bcr_validation_block_presubmit(modules)


def upload_jobs_to_pipeline(pipeline_steps):
    """Directly calling the buildkite-agent to upload steps."""
    subprocess.run(
        ["buildkite-agent", "pipeline", "upload"],
        input=yaml.dump({"steps": pipeline_steps}).encode(),
        check=True,
    )


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

    test_module_runner = subparsers.add_parser("test_module_runner")
    test_module_runner.add_argument("--module_name", type=str)
    test_module_runner.add_argument("--module_version", type=str)
    test_module_runner.add_argument("--task", type=str)

    args = parser.parse_args(argv)
    if args.subparsers_name == "bcr_presubmit":
        modules = get_target_modules()
        if not modules:
            bazelci.eprint("No target module versions detected in this branch!")
        pipeline_steps = []
        for module_name, module_version in modules:
            configs = get_task_config(module_name, module_version)
            add_presubmit_jobs(module_name, module_version, configs.get("tasks", {}), pipeline_steps)
            configs = get_test_module_task_config(module_name, module_version)
            add_presubmit_jobs(module_name, module_version, configs.get("tasks", {}), pipeline_steps, is_test_module=True)
        if should_wait_bcr_maintainer_review(modules):
            if pipeline_steps:
                pipeline_steps = [{"block": "Wait on BCR maintainer review", "blocked_state": "failed"}] + pipeline_steps
        upload_jobs_to_pipeline(pipeline_steps)
    elif args.subparsers_name == "runner":
        repo_location = create_simple_repo(args.module_name, args.module_version, args.task)
        config_file = get_presubmit_yml(args.module_name, args.module_version)
        return run_test(repo_location, config_file, args.task)
    elif args.subparsers_name == "test_module_runner":
        repo_location, config_file = prepare_test_module_repo(args.module_name, args.module_version, args.task)
        return run_test(repo_location, config_file, args.task)
    else:
        parser.print_help()
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
