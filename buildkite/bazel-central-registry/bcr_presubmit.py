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
import requests
import yaml

import bazelci

BCR_REPO_DIR = pathlib.Path(os.getcwd())

BUILDKITE_ORG = os.environ.get("BUILDKITE_ORGANIZATION_SLUG", "bazel")

SCRIPT_URL = "https://raw.githubusercontent.com/bazelbuild/continuous-integration/{}/buildkite/bazel-central-registry/bcr_presubmit.py?{}".format(
    bazelci.GITHUB_BRANCH, int(time.time())
)

CI_MACHINE_NUM = {
    "bazel": {
        "default": 140,
        "windows": 30,
        "macos_arm64": 95,
        "macos": 138,
        "arm64": 55,
    },
    "bazel-testing": {
        "default": 10,
        "windows": 10,
        "macos_arm64": 2,
        "macos": 10,
        "arm64": 5,
    },
}[BUILDKITE_ORG]

# The percentage of CI resource that can be used by bcr-presubmit and bcr-compatibility pipelines.
CI_RESOURCE_PERCENTAGE = int(os.environ.get('CI_RESOURCE_PERCENTAGE', -1))


def fetch_bcr_presubmit_py_command():
    return "curl -s {0} -o bcr_presubmit.py".format(SCRIPT_URL)


class BcrPipelineException(Exception):
    """Raised whenever something goes wrong and we should exit with an error."""


def error(msg):
    bazelci.eprint("\x1b[31mERROR\x1b[0m: {}\n".format(msg))
    raise BcrPipelineException("BCR Presubmit failed!")


def get_target_modules():
    """
    Calculate target modules based on changed files from the main branch.
    """
    # Get the list of changed files compared to the main branch
    output = subprocess.check_output(
        ["git", "diff", "main...HEAD", "--name-only", "--pretty=format:"]
    )
    modules = set()
    # Matching modules/<name>/<version>/
    for line in output.decode("utf-8").split():
        s = re.match(r"modules\/([^\/]+)\/([^\/]+)\/", line)
        if s:
            modules.add(s.groups())

    return sorted(modules)


def get_modules_with_metadata_change():
    """
    Calculate modules with metadata change from the main branch.
    """
    # Get the list of changed files compared to the main branch
    output = subprocess.check_output(
        ["git", "diff", "main...HEAD", "--name-only", "--pretty=format:"]
    )
    modules = set()
    # Matching modules/<name>/metadata.json
    for line in output.decode("utf-8").split():
        s = re.match(r"modules\/([^\/]+)\/metadata\.json", line)
        if s:
            modules.add(s.groups()[0])

    return sorted(modules)


def get_metadata_json(module_name):
    return BCR_REPO_DIR.joinpath("modules/%s/metadata.json" % module_name)


def get_presubmit_yml(module_name, module_version):
    return BCR_REPO_DIR.joinpath("modules/%s/%s/presubmit.yml" % (module_name, module_version))


def get_module_dot_bazel(module_name, module_version):
    return BCR_REPO_DIR.joinpath("modules/%s/%s/MODULE.bazel" % (module_name, module_version))


def get_source_json(module_name, module_version):
    return BCR_REPO_DIR.joinpath("modules/%s/%s/source.json" % (module_name, module_version))


def get_patch_file(module_name, module_version, patch):
    return BCR_REPO_DIR.joinpath("modules/%s/%s/patches/%s" % (module_name, module_version, patch))

def get_overlay_file(module_name, module_version, filename):
    return BCR_REPO_DIR.joinpath("modules/%s/%s/overlay/%s" % (module_name, module_version, filename))

def get_anonymous_module_task_config(module_name, module_version, bazel_version=None):
    return bazelci.load_config(http_url=None,
                               file_config=get_presubmit_yml(module_name, module_version),
                               allow_imports=False,
                               bazel_version=bazel_version)

def get_test_module_task_config(module_name, module_version, bazel_version=None):
    orig_presubmit = yaml.safe_load(open(get_presubmit_yml(module_name, module_version), "r"))
    if "bcr_test_module" in orig_presubmit:
        config = orig_presubmit["bcr_test_module"]
        bazelci.maybe_overwrite_bazel_version(bazel_version, config)
        bazelci.expand_task_config(config)
        return config
    return {}


def add_presubmit_jobs(module_name, module_version, task_configs, pipeline_steps, is_test_module=False, overwrite_bazel_version=None, low_priority=False):
    for task_id, task_config in task_configs.items():
        platform_name = get_platform(task_id, task_config)
        platform_label = bazelci.PLATFORMS[platform_name]["emoji-name"]
        task_name = task_config.get("name", "")
        label = f"{module_name}@{module_version} - {platform_label} - {task_name}"
        # The bazel version should always be set in the task config due to https://github.com/bazelbuild/bazel-central-registry/pull/1387
        # But fall back to empty string for more robustness.
        bazel_version = task_config.get("bazel", "")
        if bazel_version and not overwrite_bazel_version:
            label = f":bazel:{bazel_version} - {label}"
        command = (
            '%s bcr_presubmit.py %s --module_name="%s" --module_version="%s" --task=%s %s'
            % (
                bazelci.PLATFORMS[platform_name]["python"],
                "test_module_runner" if is_test_module else "anonymous_module_runner",
                module_name,
                module_version,
                task_id,
                "--overwrite_bazel_version=%s" % overwrite_bazel_version if overwrite_bazel_version else ""
            )
        )
        commands = [bazelci.fetch_bazelcipy_command(), fetch_bcr_presubmit_py_command(), command]
        queue = bazelci.PLATFORMS[platform_name].get("queue", "default")
        if CI_RESOURCE_PERCENTAGE == -1:
            concurrency = concurrency_group = None
        else:
            concurrency = max(1, (CI_RESOURCE_PERCENTAGE * CI_MACHINE_NUM[queue]) // 100)
            concurrency_group = f"bcr-presubmit-test-queue-{queue}"
        if low_priority:
            concurrency = 5 if concurrency is None else min(5, concurrency)
            concurrency_group = f"bcr-presubmit-test-queue-{queue}-low-priority"
        pipeline_steps.append(bazelci.create_step(label, commands, platform_name, concurrency=concurrency, concurrency_group=concurrency_group, priority=-100 if low_priority else None))


def get_platform(task_id, task_config):
    original = bazelci.get_platform_for_task(task_id, task_config)
    # TODO(#2272): delete once centos references have been deleted
    # from BCR templates in all module repos.
    return original.replace("centos7", "rockylinux8")


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


def create_anonymous_repo(module_name, module_version, root=None):
    """Create an anonymous Bazel module which depends on the target module."""
    if not root:
        root = pathlib.Path(bazelci.get_repositories_root())
    root.mkdir(exist_ok=True, parents=True)
    scratch_file(root, "WORKSPACE")
    scratch_file(root, "BUILD")
    scratch_file(root, "MODULE.bazel", ["bazel_dep(name = '%s', version = '%s')" % (module_name, module_version)])
    scratch_file(root, ".bazelrc", [
        "common --enable_bzlmod",
        "common --registry=%s" % BCR_REPO_DIR.as_uri(),
    ])
    return root


def read(path):
    with open(path, "r") as file:
        return file.read()


def prepare_test_module_repo(module_name, module_version, overwrite_bazel_version=None, root=None, suppress_log=False):
    """Prepare the test module repo and the presubmit yml file it should use"""
    suppress_log or bazelci.print_collapsed_group(":information_source: Prepare test module repo")
    if not root:
        root = pathlib.Path(bazelci.get_repositories_root())

    # Prepare the source tree by vendoring the module's repo so we get the exact source tree generated by Bazel.
    suppress_log or bazelci.eprint("* Preparing test module source with Bazel")
    anonymous_module_root = create_anonymous_repo(module_name, module_version, root = root.joinpath(".temp_anonymous_module"))
    bazelci.execute_command(["bazel", "--batch"] + bazelci.common_startup_flags()
                            + ["vendor", "--vendor_dir=./vendor_src", "--repository_cache=", "--lockfile_mode=off", "--repo", f"@{module_name}"],
                            cwd=anonymous_module_root,
                            env={**os.environ, "USE_BAZEL_VERSION": "latest"})
    source_root = root.joinpath("module_src")
    suppress_log or bazelci.eprint(f"* Moving vendored module source to {source_root}")
    shutil.move(anonymous_module_root.joinpath(f"vendor_src/{module_name}+"), source_root)

    # Generate the presubmit.yml file for the test module, it should be the content under "bcr_test_module"
    orig_presubmit = yaml.safe_load(open(get_presubmit_yml(module_name, module_version), "r"))
    test_module_presubmit = root.joinpath("presubmit.yml")
    with open(test_module_presubmit, "w") as f:
        yaml.dump(orig_presubmit["bcr_test_module"], f)
    suppress_log or bazelci.eprint("* Generate test module presubmit.yml:\n%s\n" % read(test_module_presubmit))

    # Write necessary options to the .bazelrc file
    test_module_root = source_root.joinpath(orig_presubmit["bcr_test_module"]["module_path"])

    # Check if test_module_root is a directory
    if not test_module_root.is_dir():
        error("The test module directory does not exist in the source archive: %s" % test_module_root)

    scratch_file(test_module_root, ".bazelrc", [
        # .bazelrc may not end with a newline.
        "",
        "common --enable_bzlmod",
        "common --registry=%s" % BCR_REPO_DIR.as_uri(),
        # In case the test module sets --check_direct_dependencies=error and a different Bazel version may trigger the error.
        "common --check_direct_dependencies=warning" if overwrite_bazel_version else "",
    ], mode="a")
    suppress_log or bazelci.eprint("* Append Bzlmod flags to .bazelrc file:\n%s\n" % read(test_module_root.joinpath(".bazelrc")))

    suppress_log or bazelci.eprint("* Test module ready: %s\n" % test_module_root)
    return test_module_root, test_module_presubmit


def run_test(repo_location, task_config_file, task, overwrite_bazel_version=None):
    try:
        return_code = bazelci.main(
            [
                "runner",
                "--task=" + task,
                "--file_config=%s" % task_config_file,
                "--repo_location=%s" % repo_location,
            ] + (["--overwrite_bazel_version=%s" % overwrite_bazel_version] if overwrite_bazel_version else [])
        )
        if return_code == 73 and os.environ.get("ENABLE_BAZELISK_MIGRATE"):
            bazelci.eprint(
            "\n\x1b[31mERROR\x1b[0m: BCR presubmit failed with incompatible flags.\n"
            "Please consider migrating your project for the incompatible flags.\n"
            "You can bypass this test by commenting '@bazel-io skip_check incompatible_flags' in the PR or override the list of flags in your presubmit.yml file.\n"
            "See more details at https://github.com/bazelbuild/bazel-central-registry/blob/main/docs/README.md#testing-incompatible-flags"
            )
        return return_code
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
        re.compile(r"modules\/([^\/]+)\/([^\/]+)\/overlay"),
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


def get_labels_from_pr():
    """Get the labels from the PR and return them as a list of strings."""

    # https://buildkite.com/docs/pipelines/environment-variables#BUILDKITE_PULL_REQUEST
    pr_number = os.environ.get("BUILDKITE_PULL_REQUEST")
    if not pr_number or pr_number == "false":
        return []

    tries = 5
    for attempt in range(1, tries + 1):
        response = requests.get(f"https://api.github.com/repos/bazelbuild/bazel-central-registry/pulls/{pr_number}")
        if response.status_code == 200:
            pr = response.json()
            return [label["name"] for label in pr["labels"]]

        if response.status_code not in [429, 403] or attempt >= tries:
            error(f"Error: {response.status_code}. Could not fetch labels for PR https://github.com/bazelbuild/bazel-central-registry/pull/{pr_number}")

        time.sleep(1.0 * attempt)


def should_bcr_validation_block_presubmit(modules, modules_with_metadata_change, pr_labels):
    bazelci.print_collapsed_group("Running BCR validations:")
    if not modules and not modules_with_metadata_change:
        bazelci.eprint("No modules to validate.")
        return False
    skip_validation_flags = []
    if "skip-source-repo-check" in pr_labels:
        skip_validation_flags.append("--skip_validation=source_repo")
    if "skip-url-stability-check" in pr_labels:
        skip_validation_flags.append("--skip_validation=url_stability")
    if "skip-compatibility-level-check" in pr_labels:
        skip_validation_flags.append("--skip_validation=compatibility_level")
    if "presubmit-auto-run" in pr_labels:
        skip_validation_flags.append("--skip_validation=presubmit_yml")
    returncode = subprocess.run(
        ["python3", "./tools/bcr_validation.py"]
        + [f"--check_metadata={module}" for module in modules_with_metadata_change]
        + [f"--check={name}@{version}" for name, version in modules] + skip_validation_flags,
    ).returncode
    # When a BCR maintainer view is required, the script should return 42.
    if returncode == 42:
        return True
    if returncode != 0:
        raise BcrPipelineException("BCR validation failed!")
    return False


def file_exists_in_main_branch(file_path):
    # Run the git ls-tree command to check for the file in the main branch
    result = subprocess.run(
        ["git", "ls-tree", "-r", "main", "--name-only", file_path],
        capture_output=True, text=True, check=True
    )
    return result.stdout.strip() != ""


def should_metadata_change_block_presubmit(modules_with_metadata_change, pr_labels):
    # Skip the metadata.json check if the PR is labeled with "presubmit-auto-run".
    if "presubmit-auto-run" in pr_labels:
        return False

    bazelci.print_expanded_group("Checking metadata.json file changes:")

    # If information like, maintainers, homepage, repository is changed, the presubmit should wait for a BCR maintainer review.
    # For each changed module, check if anything other than the "versions" field is changed in the metadata.json file.
    needs_bcr_maintainer_review = False
    for name in modules_with_metadata_change:
        metadata_json = get_metadata_json(name)

        if not file_exists_in_main_branch(metadata_json):
            bazelci.eprint("\x1b[33mWARNING\x1b[0m: The metadata.json file for '%s' is newly created!\n" % name)
            needs_bcr_maintainer_review = True
            continue

        # Read the new metadata.json file.
        metadata_new = json.load(open(metadata_json, "r"))

        # Check out and read the original metadata.json file from the main branch.
        subprocess.run(["git", "checkout", "main", "--", metadata_json], check=True)
        metadata_old = json.load(open(metadata_json, "r"))

        # Revert the metadata.json file to the HEAD of current branch.
        subprocess.run(["git", "checkout", "HEAD", "--", metadata_json], check=True)

        # Clear the "versions" field and compare the rest of the metadata.json file.
        metadata_old["versions"] = []
        metadata_new["versions"] = []
        if metadata_old != metadata_new:
            bazelci.eprint("\x1b[33mWARNING\x1b[0m: The change in metadata.json file for '%s' needs BCR maintainer review!\n" % name)
            needs_bcr_maintainer_review = True
        else:
            bazelci.eprint("The change in metadata.json file for '%s' looks good!\n" % name)

    return needs_bcr_maintainer_review


def should_wait_bcr_maintainer_review(modules, pr_labels):
    """Validate the changes and decide whether the presubmit should wait for a BCR maintainer review.
    Returns False if all changes look good and the presubmit can proceed.
    Returns True if the changes should block follow up presubmit jobs until a BCR maintainer triggers them.
    Throws an error if the changes violate BCR policies or the BCR validations fail.
    """
    # If existing modules are changed, fail the presubmit.
    validate_existing_modules_are_not_modified()

    # If files outside of the modules/ directory are changed, fail the presubmit.
    validate_files_outside_of_modules_dir_are_not_modified(modules)

    # Get modules with metadata.json changes.
    modules_with_metadata_change = get_modules_with_metadata_change()

    # Check if any changes in the metadata.json file need a manual review.
    needs_bcr_maintainer_review = should_metadata_change_block_presubmit(modules_with_metadata_change, pr_labels)

    # Run BCR validations on target modules and decide if the presubmit jobs should be blocked.
    if should_bcr_validation_block_presubmit(modules, modules_with_metadata_change, pr_labels):
        needs_bcr_maintainer_review = True

    return needs_bcr_maintainer_review


def get_bazel_version_for_task(config_file, task, overwrite_bazel_version=None):
    """
    Determine the Bazel version to use for a specific task.
    """
    if overwrite_bazel_version:
        return overwrite_bazel_version
    configs = bazelci.fetch_configs(None, config_file)
    task_config = configs.get("tasks", {}).get(task, {})
    bazelci.eprint(f"Task config for '{task}':")
    bazelci.eprint(yaml.dump(task_config, default_flow_style=False))
    bazel_version = task_config.get("bazel", "latest")
    return bazel_version


def fetch_incompatible_flags(module_name, module_version, bazel_version):
    """
    Fetch incompatible flags for a given module and version.
    """
    bazelci.print_collapsed_group(":information_source: Fetching incompatible flags")
    incompatible_flags = []
    for file_path in [get_presubmit_yml(module_name, module_version), BCR_REPO_DIR.joinpath("incompatible_flags.yml")]:
        if file_path.exists():
            with open(file_path, "r") as file:
                data = yaml.safe_load(file)
            if isinstance(data.get("incompatible_flags"), dict):
                for flag, versions in data["incompatible_flags"].items():
                    if bazel_version in versions:
                        incompatible_flags.append(flag)
                bazelci.eprint(f"Fetched incompatible flags from {file_path} for Bazel version {bazel_version}: {incompatible_flags}")
                return incompatible_flags
    return []


def maybe_enable_bazelisk_migrate(module_name, module_version, overwrite_bazel_version, task, config_file):
    # Only try to set up bazelisk --migrate when ENABLE_BAZELISK_MIGRATE is specified.
    # ENABLE_BAZELISK_MIGRATE should be set for the BCR presubmit pipeline but not for the BCR compatibility test pipeline, which also depends on bcr_presubmit.py
    if not os.environ.get("ENABLE_BAZELISK_MIGRATE"):
        return

    bazelci.print_collapsed_group(":triangular_flag_on_post: Set up env vars for incompatible flags test if enabled")
    pr_labels = get_labels_from_pr()
    if "skip-incompatible-flags-test" in pr_labels:
        bazelci.eprint("Skipping incompatible flags test as 'skip-incompatible-flags-test' label is attached to this PR.")
        return

    bazel_version = get_bazel_version_for_task(config_file, task, overwrite_bazel_version)
    incompatible_flags = fetch_incompatible_flags(module_name, module_version, bazel_version)
    if not incompatible_flags:
        bazelci.eprint(f"No incompatible flags found for Bazel version {bazel_version}.")
        return

    os.environ["USE_BAZELISK_MIGRATE"] = "1"
    os.environ["INCOMPATIBLE_FLAGS"] = ",".join(incompatible_flags)
    bazelci.eprint(f"USE_BAZELISK_MIGRATE is set to {os.environ['USE_BAZELISK_MIGRATE']}")
    bazelci.eprint(f"INCOMPATIBLE_FLAGS are set to {os.environ['INCOMPATIBLE_FLAGS']}")


def upload_jobs_to_pipeline(pipeline_steps):
    """Upload jobs to Buildkite in batches."""
    BATCH_SIZE = 2000

    # Make sure all jobs depends on the block step explicitly
    # if we need multiple batches and the first step is a block step.
    if len(pipeline_steps) > BATCH_SIZE and "block" in pipeline_steps[0]:
        pipeline_steps[0]["key"] = "wait_for_approval"
        for step in pipeline_steps[1:]:
            step["depends_on"] = "wait_for_approval"

    for i in range(0, len(pipeline_steps), BATCH_SIZE):
        batch = pipeline_steps[i:i + BATCH_SIZE]
        # Upload the batch to Buildkite
        bazelci.eprint(f"Uploading batch {i // BATCH_SIZE + 1} of {len(pipeline_steps) // BATCH_SIZE + 1}")
        try:
            subprocess.run(
                ["buildkite-agent", "pipeline", "upload"],
                input=yaml.dump({"steps": batch}).encode(),
                check=True,
            )
        except subprocess.CalledProcessError as e:
            error(f"Failed to upload batch {i // BATCH_SIZE + 1} to Buildkite: {e}")


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Bazel Central Registry Presubmit Test Generator")

    subparsers = parser.add_subparsers(dest="subparsers_name")

    subparsers.add_parser("bcr_presubmit")

    anonymous_module_runner = subparsers.add_parser("anonymous_module_runner")
    anonymous_module_runner.add_argument("--module_name", type=str)
    anonymous_module_runner.add_argument("--module_version", type=str)
    anonymous_module_runner.add_argument("--overwrite_bazel_version", type=str)
    anonymous_module_runner.add_argument("--task", type=str)

    test_module_runner = subparsers.add_parser("test_module_runner")
    test_module_runner.add_argument("--module_name", type=str)
    test_module_runner.add_argument("--module_version", type=str)
    test_module_runner.add_argument("--overwrite_bazel_version", type=str)
    test_module_runner.add_argument("--task", type=str)

    args = parser.parse_args(argv)

    if args.subparsers_name == "bcr_presubmit":
        modules = get_target_modules()
        if not modules:
            bazelci.eprint("No target module versions detected in this branch!")

        pr_labels = get_labels_from_pr()
        low_priority = "low-ci-priority" in pr_labels
        pipeline_steps = []
        for module_name, module_version in modules:
            previous_size = len(pipeline_steps)

            configs = get_anonymous_module_task_config(module_name, module_version)
            add_presubmit_jobs(module_name, module_version, configs.get("tasks", {}), pipeline_steps, low_priority=low_priority)
            configs = get_test_module_task_config(module_name, module_version)
            add_presubmit_jobs(module_name, module_version, configs.get("tasks", {}), pipeline_steps, is_test_module=True, low_priority=low_priority)

            if len(pipeline_steps) == previous_size:
                error("No pipeline steps generated for %s@%s. Please check the configuration." % (module_name, module_version))

        if should_wait_bcr_maintainer_review(modules, pr_labels):
            pipeline_steps.insert(0, {"block": "Wait on BCR maintainer review", "blocked_state": "running"})

        upload_jobs_to_pipeline(pipeline_steps)
    elif args.subparsers_name == "anonymous_module_runner":
        repo_location = create_anonymous_repo(args.module_name, args.module_version)
        config_file = get_presubmit_yml(args.module_name, args.module_version)
        maybe_enable_bazelisk_migrate(args.module_name, args.module_version, args.overwrite_bazel_version, args.task, config_file)
        return run_test(repo_location, config_file, args.task, args.overwrite_bazel_version)
    elif args.subparsers_name == "test_module_runner":
        repo_location, config_file = prepare_test_module_repo(args.module_name, args.module_version, args.overwrite_bazel_version)
        maybe_enable_bazelisk_migrate(args.module_name, args.module_version, args.overwrite_bazel_version, args.task, config_file)
        return run_test(repo_location, config_file, args.task, args.overwrite_bazel_version)
    else:
        parser.print_help()
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
