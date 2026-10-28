#!/usr/bin/env python3
#
# Copyright 2026 The Bazel Authors. All rights reserved.
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
"""The CI script for Bazel Central Registry Downstream Test pipeline."""

import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import yaml

import bazelci
import bcr_presubmit

SCRIPT_URL = "https://raw.githubusercontent.com/bazelbuild/continuous-integration/{}/buildkite/bazel-central-registry/bcr_downstream.py?{}".format(
    bazelci.GITHUB_REF, int(time.time())
)

# Limit CI resource consumption by default (10% of machines per queue) so
# downstream test builds do not starve bcr-presubmit.
DEFAULT_CI_RESOURCE_PERCENTAGE = 10
CI_RESOURCE_PERCENTAGE = int(
    os.environ.get("CI_RESOURCE_PERCENTAGE", DEFAULT_CI_RESOURCE_PERCENTAGE)
)

# Default maximum number of direct downstream modules to select by PageRank.
DEFAULT_TOP_BCR_MODULES = 50

# `bazel vendor` is only available since Bazel 7.
MIN_VENDOR_BAZEL_MAJOR_VERSION = 7


def fetch_bcr_downstream_py_command():
    return bazelci.curl_download_command(SCRIPT_URL, "bcr_downstream.py")


def parse_module(value):
    """Parse and validate a module in "<name>@<version>" format."""
    name, _, version = value.strip().partition("@")
    if not bcr_presubmit.is_valid_module_identifier(name, version):
        raise ValueError(f"Invalid module (expected <name>@<version>): {value!r}")
    return name, version


# Matches the major version of a pinned or wildcard Bazel version, e.g. "8.x", "8.*", "8.4.2",
# "9.0.0rc1" or "10.0.0-pre.20260911.2".
BAZEL_MAJOR_VERSION_RE = re.compile(r"^(\d+)(?:\.|$)")


def get_bazel_major_version(bazel_version):
    """Return the major version of a Bazel version, or None for symbolic ones like "rolling"."""
    m = BAZEL_MAJOR_VERSION_RE.match(str(bazel_version).strip())
    return int(m.group(1)) if m else None


# Pipeline generation (`bcr_downstream.py bcr_downstream`).


def select_module_versions(selections, random_percentage=None):
    """Resolve module selection patterns (e.g. "grpc@latest") using ./tools/module_selector.py."""
    args = [f"--select={s}" for s in selections]
    if random_percentage:
        args.append(f"--random-percentage={random_percentage}")
    output = subprocess.check_output(
        ["python3", "./tools/module_selector.py"] + args,
        cwd=bcr_presubmit.BCR_REPO_DIR,
    )
    return sorted({parse_module(line) for line in output.decode("utf-8").split()})


def get_target_module():
    """Return the target (module_name, module_version) to test downstream dependents for.

    It's resolved from the TARGET_MODULE env var (e.g. "protobuf@latest") if it is set, or detected
    from the files changed on the current branch otherwise. Returns None if there is no target.
    """
    selection = os.environ.get("TARGET_MODULE", "").strip()
    if selection:
        target_modules = select_module_versions([selection])
    else:
        target_modules = bcr_presubmit.get_target_modules()
    if len(target_modules) > 1:
        found = ", ".join(f"{name}@{version}" for name, version in target_modules)
        bcr_presubmit.error(
            f"Only one target module can be tested in a build, found: {found}. "
            "Please set TARGET_MODULE to choose one."
        )
    return target_modules[0] if target_modules else None


# Characters allowed in a Bazel version (e.g. "8.x", "9.0.0rc1", "last_green" or "<fork>/latest"),
# which also makes sure the version can be safely used in step commands.
BAZEL_VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._*/+-]*$")


def parse_int_option(name, value, min_value, max_value=None):
    try:
        number = int(str(value).strip())
    except ValueError:
        number = None
    if number is None or number < min_value or (max_value is not None and number > max_value):
        expected = f">= {min_value}" if max_value is None else f"from {min_value} to {max_value}"
        bcr_presubmit.error(f"Invalid {name}: {value!r}, expected an integer {expected}.")
    return number


def parse_bool_option(name, value):
    normalized = str(value).strip().lower()
    if normalized not in ("1", "true", "yes", "0", "false", "no"):
        bcr_presubmit.error(f"Invalid {name}: {value!r}, expected true or false.")
    return normalized in ("1", "true", "yes")


def parse_list_option(name, value):
    if isinstance(value, str):
        value = value.split(",")
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        bcr_presubmit.error(f"Invalid {name}: {value!r}, expected a list of strings.")
    return tuple(v.strip() for v in value if v.strip())


def parse_bazel_version_option(name, value):
    version = str(value).strip()
    if not BAZEL_VERSION_RE.match(version):
        bcr_presubmit.error(f"Invalid {name}: {value!r}, expected a Bazel version such as 8.x.")
    return version


# Options of the downstream test as {name: (default, parser)}. The target module can set them in its
# presubmit.yml under `bcr_downstream_test`, the environment variables with the same names in upper
# case (e.g. SELECT_TOP_BCR_MODULES) take precedence when set.
DOWNSTREAM_TEST_CONFIG_KEY = "bcr_downstream_test"
DOWNSTREAM_TEST_OPTIONS = {
    "select_top_bcr_modules": (DEFAULT_TOP_BCR_MODULES, lambda n, v: parse_int_option(n, v, 0)),
    "module_selections": ((), parse_list_option),
    "smoke_test_percentage": (None, lambda n, v: parse_int_option(n, v, 1, 100)),
    "exclude_dev_deps": (False, parse_bool_option),
    "use_bazel_version": (None, parse_bazel_version_option),
}


def get_downstream_test_options(module_name, module_version):
    """Return the downstream test options for the target module.

    Each option comes from its environment variable if it's set, otherwise from the target module's
    presubmit.yml, otherwise its default value.
    """
    target = f"{module_name}@{module_version}"
    with open(bcr_presubmit.get_presubmit_yml(module_name, module_version), "r") as f:
        config = (yaml.safe_load(f) or {}).get(DOWNSTREAM_TEST_CONFIG_KEY) or {}
    if not isinstance(config, dict):
        bcr_presubmit.error(
            f"`{DOWNSTREAM_TEST_CONFIG_KEY}` in the presubmit.yml of {target} must be a map."
        )
    unknown_keys = sorted(str(k) for k in config if k not in DOWNSTREAM_TEST_OPTIONS)
    if unknown_keys:
        bcr_presubmit.error(
            f"Unknown option(s) {unknown_keys} under `{DOWNSTREAM_TEST_CONFIG_KEY}` in the "
            f"presubmit.yml of {target}, supported options are {list(DOWNSTREAM_TEST_OPTIONS)}."
        )
    options = {}
    for key, (default, parse) in DOWNSTREAM_TEST_OPTIONS.items():
        env_value = os.environ.get(key.upper(), "").strip()
        if env_value:
            options[key] = parse(key.upper(), env_value)
        elif config.get(key) is not None:
            options[key] = parse(f"{DOWNSTREAM_TEST_CONFIG_KEY}.{key} of {target}", config[key])
        else:
            options[key] = default
    customized = {k: v for k, v in options.items() if v != DOWNSTREAM_TEST_OPTIONS[k][0]}
    bazelci.eprint(f"* Downstream test options: {customized or 'defaults'}")
    return options


def get_top_dependents(module_name, top_n, exclude_dev_deps):
    """Return the top N direct dependents of a module ranked by BCR PageRank."""
    # Remove USE_BAZEL_VERSION to make this step more stable.
    env = os.environ.copy()
    env.pop("USE_BAZEL_VERSION", None)
    cmd = ["bazel", "run", "//tools:module_analyzer", "--", "--name-only", f"--top_n={top_n}"]
    if exclude_dev_deps:
        cmd.append("--exclude-dev-deps")
    cmd.append(f"--dependents_of={module_name}")
    output = subprocess.check_output(cmd, cwd=bcr_presubmit.BCR_REPO_DIR, env=env)
    return output.decode("utf-8").split()


def select_downstream_modules(target_name, options):
    """Return the downstream module versions to test against the target module."""
    selections = options["module_selections"]
    if not selections and options["select_top_bcr_modules"]:
        dependents = get_top_dependents(
            target_name, options["select_top_bcr_modules"], options["exclude_dev_deps"]
        )
        selections = [f"{m}@latest" for m in dependents]
    if not selections:
        return []

    modules = select_module_versions(selections, options["smoke_test_percentage"])
    if modules:
        bazelci.print_expanded_group(
            "The following downstream modules are selected:\n\n%s"
            % "\n".join([f"{name}@{version}" for name, version in modules])
        )
    return modules


def get_task_bazel_versions(module_name, module_version):
    """Return the Bazel versions used by a module's presubmit tasks, including bcr_test_module."""
    configs = [
        bcr_presubmit.get_anonymous_module_task_config(module_name, module_version),
        bcr_presubmit.get_test_module_task_config(module_name, module_version),
    ]
    return {
        str(task_config["bazel"])
        for config in configs
        for task_config in config.get("tasks", {}).values()
        if task_config.get("bazel")
    }


def get_target_bazel_major_versions(module_name, module_version):
    """Return the Bazel major versions tested by the target module's presubmit.yml.

    Returns (majors, tests_newest), where `majors` are the major versions of the pinned Bazel
    versions (e.g. {8, 9} for "8.x" and "9.*"), and `tests_newest` tells whether the target is also
    tested with a symbolic version (e.g. "rolling", "last_green") tracking the newest Bazel, in
    which case any major version newer than the highest pinned one is considered tested too.
    Returns None if the target module doesn't pin any Bazel version, so that no task is filtered.
    """
    target = f"{module_name}@{module_version}"
    versions = get_task_bazel_versions(module_name, module_version)
    majors = {get_bazel_major_version(v) for v in versions} - {None}
    symbolic_versions = sorted(v for v in versions if get_bazel_major_version(v) is None)
    if not majors:
        bazelci.eprint(
            f"* Not filtering downstream tasks by Bazel version for {target}: no pinned Bazel "
            f"version in its presubmit.yml (found {symbolic_versions})"
        )
        return None
    message = f"* {target} is tested with Bazel major versions {sorted(majors)}"
    if symbolic_versions:
        message += f" and {', '.join(symbolic_versions)}, newer major versions are also allowed"
    bazelci.eprint(message)
    return majors, bool(symbolic_versions)


def filter_tasks_by_bazel_major_versions(module_name, module_version, task_configs, tested_majors):
    """Drop tasks whose Bazel major version is not tested by the target module."""
    if not tested_majors:
        return task_configs
    majors, tests_newest = tested_majors
    filtered = {}
    for task_id, task_config in task_configs.items():
        bazel_version = task_config.get("bazel")
        major = get_bazel_major_version(bazel_version)
        # Keep tasks whose major version can't be determined statically (e.g. "latest", "rolling").
        if major is None or major in majors or (tests_newest and major > max(majors)):
            filtered[task_id] = task_config
        else:
            bazelci.eprint(
                f"* Skipping {module_name}@{module_version} task {task_id!r}: "
                f"Bazel {bazel_version} is not tested by the target module"
            )
    return filtered


def create_downstream_steps(
    module_name,
    module_version,
    target,
    task_configs,
    is_test_module,
    overwrite_bazel_version,
    low_priority,
):
    """Return the steps running tasks of a downstream module against the target module."""
    steps = []
    for task_id, task_config in task_configs.items():
        platform_name = bcr_presubmit.get_platform(task_id, task_config)
        platform_label = bazelci.PLATFORMS[platform_name]["emoji-name"]
        task_name = task_config.get("name", "")
        label = f"{module_name}@{module_version} (with {target}) - {platform_label} - {task_name}"
        bazel_version = task_config.get("bazel", "")
        if bazel_version and not overwrite_bazel_version:
            label = f":bazel:{bazel_version} - {label}"

        command = [
            bazelci.PLATFORMS[platform_name]["python"],
            "bcr_downstream.py",
            "test_module_runner" if is_test_module else "anonymous_module_runner",
            f'--module="{module_name}@{module_version}"',
            f'--target_module="{target}"',
            f"--task={task_id}",
        ]
        if overwrite_bazel_version:
            command.append(f'--overwrite_bazel_version="{overwrite_bazel_version}"')
        commands = [
            bazelci.fetch_ci_scripts_command(),
            bcr_presubmit.fetch_bcr_presubmit_py_command(),
            fetch_bcr_downstream_py_command(),
            " ".join(command),
        ]
        queue = bazelci.PLATFORMS[platform_name].get("queue", "default")
        if CI_RESOURCE_PERCENTAGE == -1:
            concurrency = concurrency_group = None
        else:
            concurrency = max(
                1, (CI_RESOURCE_PERCENTAGE * bcr_presubmit.CI_MACHINE_NUM[queue]) // 100
            )
            concurrency_group = f"bcr-downstream-test-queue-{queue}"
        if low_priority:
            concurrency = 5 if concurrency is None else min(5, concurrency)
            concurrency_group = f"bcr-downstream-test-queue-{queue}-low-priority"

        steps.append(
            bazelci.create_step(
                label,
                commands,
                platform_name,
                concurrency=concurrency,
                concurrency_group=concurrency_group,
                priority=-100 if low_priority else -50,
            )
        )
    return steps


def generate_pipeline():
    """Upload the downstream test jobs for the target module to the pipeline."""
    target_module = get_target_module()
    if not target_module:
        bazelci.eprint("No target module version detected for downstream testing.")
        return
    target_name, target_version = target_module
    target = f"{target_name}@{target_version}"
    bazelci.print_expanded_group(f"Target module for downstream testing: {target}")

    options = get_downstream_test_options(target_name, target_version)
    downstream_modules = select_downstream_modules(target_name, options)
    if not downstream_modules:
        bazelci.eprint(f"No downstream modules selected for {target}.")
        return

    # An explicit Bazel version (USE_BAZEL_VERSION or `use_bazel_version`) overrides the Bazel
    # versions of all downstream tasks. Otherwise, downstream tasks with Bazel major versions not
    # tested by the target module are skipped.
    bazel_version = options["use_bazel_version"]
    if bazel_version:
        bazelci.eprint(f"* Running all downstream tasks with Bazel {bazel_version}")
        tested_majors = None
    else:
        tested_majors = get_target_bazel_major_versions(target_name, target_version)
    low_priority = "low-ci-priority" in bcr_presubmit.get_labels_from_pr()

    pipeline_steps = []
    for module_name, module_version in downstream_modules:
        for is_test_module, get_task_config in (
            (False, bcr_presubmit.get_anonymous_module_task_config),
            (True, bcr_presubmit.get_test_module_task_config),
        ):
            task_configs = get_task_config(module_name, module_version, bazel_version)
            task_configs = filter_tasks_by_bazel_major_versions(
                module_name, module_version, task_configs.get("tasks", {}), tested_majors
            )
            pipeline_steps += create_downstream_steps(
                module_name,
                module_version,
                target,
                task_configs,
                is_test_module,
                bazel_version,
                low_priority,
            )

    bcr_presubmit.upload_jobs_to_pipeline(pipeline_steps)


# Downstream task runner (`bcr_downstream.py {anonymous_module_runner,test_module_runner}`).


def get_vendor_bazel_version(bazel_version):
    """Return the Bazel version used to vendor the target module for a task.

    Use the task's own Bazel version so that the module graph is resolved the same way as in the
    downstream build, but at least Bazel 7 since `bazel vendor` doesn't exist in older versions.
    """
    bazel_version = bazel_version or "latest"
    major = get_bazel_major_version(bazel_version)
    if major is not None and major < MIN_VENDOR_BAZEL_MAJOR_VERSION:
        return f"{MIN_VENDOR_BAZEL_MAJOR_VERSION}.x"
    return bazel_version


def vendor_target_module(module_name, module_version, bazel_version, root=None):
    """Vendor the target module with `bazel vendor` and return the path of its source."""
    bazelci.print_collapsed_group(":package: Vendoring the target module for override")
    root = pathlib.Path(root or bazelci.get_repositories_root())
    root.mkdir(exist_ok=True, parents=True)

    vendor_workspace = root.joinpath(".temp_vendor_target_module")
    shutil.rmtree(vendor_workspace, ignore_errors=True)
    vendor_workspace.mkdir(exist_ok=True, parents=True)

    bcr_presubmit.scratch_file(vendor_workspace, "WORKSPACE")
    bcr_presubmit.scratch_file(vendor_workspace, "BUILD")
    bcr_presubmit.scratch_file(
        vendor_workspace,
        "MODULE.bazel",
        [f"bazel_dep(name = '{module_name}', version = '{module_version}')"],
    )
    bcr_presubmit.scratch_file(
        vendor_workspace,
        ".bazelrc",
        [
            "common --enable_bzlmod",
            "common --registry=%s" % bcr_presubmit.BCR_REPO_DIR.as_uri(),
        ],
    )

    vendor_bazel_version = get_vendor_bazel_version(bazel_version)
    bazelci.eprint(f"* Vendoring {module_name}@{module_version} with Bazel {vendor_bazel_version}")

    bazelci.execute_command(
        ["bazel", "--batch"]
        + bazelci.common_startup_flags()
        + [
            "vendor",
            "--incompatible_use_plus_in_repo_names",
            "--vendor_dir=./vendor_src",
            "--repository_cache=",
            "--lockfile_mode=off",
            # Only the source tree is needed here, the downstream build still enforces
            # bazel_compatibility (e.g. when vendoring with Bazel 7 for a Bazel 6 task).
            "--check_bazel_compatibility=warning",
            f"--repo=@{module_name}",
        ],
        cwd=vendor_workspace,
        env={**os.environ, "USE_BAZEL_VERSION": vendor_bazel_version},
    )

    vendor_src_dir = vendor_workspace.joinpath("vendor_src")
    # The canonical repo name is "<name>+", except for well-known modules such as "platforms".
    candidates = [vendor_src_dir.joinpath(d) for d in (f"{module_name}+", module_name)]
    src_dir = next((d for d in candidates if d.is_dir()), None)
    if not src_dir:
        bcr_presubmit.error(f"Cannot find the vendored source of {module_name} in {vendor_src_dir}")
    vendored_path = root.joinpath("vendored_target_module")
    shutil.rmtree(vendored_path, ignore_errors=True)
    shutil.move(src_dir, vendored_path)
    vendored_path = vendored_path.resolve()
    bazelci.eprint(f"* Vendored {module_name} to {vendored_path}")
    return vendored_path


def configure_downstream_override(repo_location, module_name, vendored_path):
    """Append --override_module and dependency flags to the downstream module's .bazelrc."""
    lines = [
        "",
        "# Override the target module with its vendored source for downstream testing",
        "common --check_direct_dependencies=warning",
        "common --lockfile_mode=update",
        # Use POSIX path separators so backslashes are not treated as escapes on Windows.
        f"common --override_module={module_name}={vendored_path.as_posix()}",
    ]
    bcr_presubmit.scratch_file(repo_location, ".bazelrc", lines, mode="a")
    bazelci.eprint("* Appended downstream override flags to .bazelrc:\n%s\n" % "\n".join(lines[1:]))


def run_downstream_task(args, is_test_module):
    """Run a presubmit task of a downstream module with the target module overridden."""
    module_name, module_version = args.module
    target_name, target_version = args.target_module
    if is_test_module:
        repo_location, config_file = bcr_presubmit.prepare_test_module_repo(
            module_name, module_version, args.overwrite_bazel_version
        )
    else:
        repo_location = bcr_presubmit.create_anonymous_repo(module_name, module_version)
        config_file = bcr_presubmit.get_presubmit_yml(module_name, module_version)
    # Vendor the target module with the same Bazel version as the task, so that
    # the target module is fetched with a Bazel version it supports.
    task_bazel_version = bcr_presubmit.get_bazel_version_for_task(
        config_file, args.task, args.overwrite_bazel_version
    )
    vendored_path = vendor_target_module(target_name, target_version, task_bazel_version)
    configure_downstream_override(repo_location, target_name, vendored_path)
    return bcr_presubmit.run_test(
        repo_location, config_file, args.task, args.overwrite_bazel_version
    )


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Bazel Central Registry Downstream Test Generator & Runner"
    )
    subparsers = parser.add_subparsers(dest="subparsers_name")

    subparsers.add_parser("bcr_downstream")

    for runner in ("anonymous_module_runner", "test_module_runner"):
        runner_parser = subparsers.add_parser(runner)
        runner_parser.add_argument("--module", type=parse_module, required=True)
        runner_parser.add_argument("--target_module", type=parse_module, required=True)
        runner_parser.add_argument("--overwrite_bazel_version", type=str)
        runner_parser.add_argument("--task", type=str, required=True)

    args = parser.parse_args(argv)

    if args.subparsers_name == "bcr_downstream":
        generate_pipeline()
        return 0
    if args.subparsers_name in ("anonymous_module_runner", "test_module_runner"):
        return run_downstream_task(
            args, is_test_module=args.subparsers_name == "test_module_runner"
        )
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
