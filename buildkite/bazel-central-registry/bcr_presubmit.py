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
import zipfile
import requests
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
        # The bazel version should always be set in the task config due to https://github.com/bazelbuild/bazel-central-registry/pull/1387
        # But fall back to empty string for more robustness.
        bazel_version = task_config.get("bazel", "")
        if bazel_version:
            label = ":bazel:{} - ".format(bazel_version) + label
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


def create_simple_repo(module_name, module_version):
    """Create a simple Bazel module repo which depends on the target module."""
    root = pathlib.Path(bazelci.get_repositories_root())
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
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
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
        ["patch", "-f", "-p%d" % patch_strip, "-i", patch_file], shell=False, check=True, env=os.environ, cwd=work_dir
    )

def extract_zip_with_permissions(zip_file_path, destination_dir):
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        for entry in zip_ref.infolist():
            zip_ref.extract(entry, destination_dir)
            file_path = os.path.join(destination_dir, entry.filename)

            # Set file permissions according to https://stackoverflow.com/questions/39296101
            if entry.external_attr >  0xffff:
                os.chmod(file_path, entry.external_attr >> 16)

def unpack_archive(archive_file, output_dir):
    # Addressing https://github.com/bazelbuild/continuous-integration/issues/1536
    if archive_file.endswith(".zip"):
        extract_zip_with_permissions(archive_file, output_dir)
    else:
        shutil.unpack_archive(archive_file, output_dir)

def prepare_test_module_repo(module_name, module_version):
    """Prepare the test module repo and the presubmit yml file it should use"""
    bazelci.print_collapsed_group(":information_source: Prepare test module repo")
    root = pathlib.Path(bazelci.get_repositories_root())
    source = load_source_json(module_name, module_version)

    # Download and unpack the source archive to ./output
    archive_url = source["url"]
    archive_file = root.joinpath(archive_url.split("/")[-1].split("?")[0])
    output_dir = root.joinpath("output")
    bazelci.eprint("* Download and unpack %s\n" % archive_url)
    download(archive_url, archive_file)
    unpack_archive(str(archive_file), output_dir)
    bazelci.eprint("Source unpacked to %s\n" % output_dir)

    # Apply overlay and patch files if there are any
    source_root = output_dir.joinpath(source["strip_prefix"] if "strip_prefix" in source else "")
    if "overlay" in source:
        bazelci.eprint("* Applying overlay")
        for overlay_path in source["overlay"]:
            bazelci.eprint("\nOverlaying %s:" % overlay_path)
            overlay_file = get_overlay_file(module_name, module_version, overlay_path)
            shutil.copy(overlay_file, source_root.joinpath(overlay_path))
    if "patches" in source:
        bazelci.eprint("* Applying patch files")
        for patch_name in source["patches"]:
            bazelci.eprint("\nApplying %s:" % patch_name)
            patch_file = get_patch_file(module_name, module_version, patch_name)
            apply_patch(source_root, source["patch_strip"], patch_file)

    # Make sure the checked-in MODULE.bazel file is used.
    checked_in_module_dot_bazel = get_module_dot_bazel(module_name, module_version)
    bazelci.eprint("\n* Copy checked-in MODULE.bazel file to source root:\n%s\n" % read(checked_in_module_dot_bazel))
    module_dot_bazel = source_root.joinpath("MODULE.bazel")
    # In case the existing MODULE.bazel has no write permission.
    if module_dot_bazel.exists():
        os.remove(module_dot_bazel)
    shutil.copy(checked_in_module_dot_bazel, module_dot_bazel)

    # Generate the presubmit.yml file for the test module, it should be the content under "bcr_test_module"
    orig_presubmit = yaml.safe_load(open(get_presubmit_yml(module_name, module_version), "r"))
    test_module_presubmit = root.joinpath("presubmit.yml")
    with open(test_module_presubmit, "w") as f:
        yaml.dump(orig_presubmit["bcr_test_module"], f)
    bazelci.eprint("* Generate test module presubmit.yml:\n%s\n" % read(test_module_presubmit))

    # Write necessary options to the .bazelrc file
    test_module_root = source_root.joinpath(orig_presubmit["bcr_test_module"]["module_path"])

    # Check if test_module_root is a directory
    if not test_module_root.is_dir():
        error("The test module directory does not exist in the source archive: %s" % test_module_root)

    scratch_file(test_module_root, ".bazelrc", [
        # .bazelrc may not end with a newline.
        "",
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

    response = requests.get(f"https://api.github.com/repos/bazelbuild/bazel-central-registry/pulls/{pr_number}")
    if response.status_code == 200:
        pr = response.json()
        return [label["name"] for label in pr["labels"]]
    else:
        error(f"Error: {response.status_code}. Could not fetch labels for PR https://github.com/bazelbuild/bazel-central-registry/pull/{pr_number}")


def should_bcr_validation_block_presubmit(modules, pr_labels):
    bazelci.print_collapsed_group("Running BCR validations:")
    skip_validation_flags = []
    if "skip-source-repo-check" in pr_labels:
        skip_validation_flags.append("--skip_validation=source_repo")
    if "skip-url-stability-check" in pr_labels:
        skip_validation_flags.append("--skip_validation=url_stability")
    if "presubmit-auto-run" in pr_labels:
        skip_validation_flags.append("--skip_validation=presubmit_yml")
    returncode = subprocess.run(
        ["python3", "./tools/bcr_validation.py", "--check_all_metadata"] + [f"--check={name}@{version}" for name, version in modules] + skip_validation_flags,
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


def should_metadata_change_block_presubmit(modules, pr_labels):
    # Skip the metadata.json check if the PR is labeled with "presubmit-auto-run".
    if "presubmit-auto-run" in pr_labels:
        return False

    bazelci.print_expanded_group("Checking metadata.json file changes:")

    # Collect changed modules from module, version pairs.
    changed_modules = set([module[0] for module in modules])

    # If information like, maintainers, homepage, repository is changed, the presubmit should wait for a BCR maintainer review.
    # For each changed module, check if anything other than the "versions" field is changed in the metadata.json file.
    needs_bcr_maintainer_review = False
    for name in changed_modules:
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


def should_wait_bcr_maintainer_review(modules):
    """Validate the changes and decide whether the presubmit should wait for a BCR maintainer review.
    Returns False if all changes look good and the presubmit can proceed.
    Returns True if the changes should block follow up presubmit jobs until a BCR maintainer triggers them.
    Throws an error if the changes violate BCR policies or the BCR validations fail.
    """
    # If existing modules are changed, fail the presubmit.
    pr_labels = get_labels_from_pr()
    if "USE-WITH-CAUTION-skip-modification-check" not in pr_labels:
        validate_existing_modules_are_not_modified()

    # If files outside of the modules/ directory are changed, fail the presubmit.
    validate_files_outside_of_modules_dir_are_not_modified(modules)

    # Check if any changes in the metadata.json file need a manual review.
    needs_bcr_maintainer_review = should_metadata_change_block_presubmit(modules, pr_labels)

    # Run BCR validations on target modules and decide if the presubmit jobs should be blocked.
    if should_bcr_validation_block_presubmit(modules, pr_labels):
        needs_bcr_maintainer_review = True

    return needs_bcr_maintainer_review


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

    parser = argparse.ArgumentParser(description="Bazel Central Registry Presubmit Test Generator")

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
            previous_size = len(pipeline_steps)

            configs = get_task_config(module_name, module_version)
            add_presubmit_jobs(module_name, module_version, configs.get("tasks", {}), pipeline_steps)
            configs = get_test_module_task_config(module_name, module_version)
            add_presubmit_jobs(module_name, module_version, configs.get("tasks", {}), pipeline_steps, is_test_module=True)

            if len(pipeline_steps) == previous_size:
                error("No pipeline steps generated for %s@%s. Please check the configuration." % (module_name, module_version))

        if should_wait_bcr_maintainer_review(modules) and pipeline_steps:
            pipeline_steps = [{"block": "Wait on BCR maintainer review", "blocked_state": "running"}] + pipeline_steps

        upload_jobs_to_pipeline(pipeline_steps)
    elif args.subparsers_name == "runner":
        repo_location = create_simple_repo(args.module_name, args.module_version)
        config_file = get_presubmit_yml(args.module_name, args.module_version)
        return run_test(repo_location, config_file, args.task)
    elif args.subparsers_name == "test_module_runner":
        repo_location, config_file = prepare_test_module_repo(args.module_name, args.module_version)
        return run_test(repo_location, config_file, args.task)
    else:
        parser.print_help()
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
