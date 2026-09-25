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

GENERATE_REPORT_URL = "https://raw.githubusercontent.com/bazelbuild/continuous-integration/{}/buildkite/bazel-central-registry/generate_report.py?{}".format(
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


def fetch_generate_report_py_command():
    return bazelci.curl_download_command(GENERATE_REPORT_URL, "generate_report.py")


# Matches the major version of a pinned or wildcard Bazel version, e.g. "8.x", "8.*", "8.4.2",
# "9.0.0rc1" or "10.0.0-pre.20260911.2".
BAZEL_MAJOR_VERSION_RE = re.compile(r"^(\d+)(?:\.|$)")


def get_bazel_major_version(bazel_version):
    """Return the major version of a Bazel version, or None for symbolic ones like "rolling"."""
    m = BAZEL_MAJOR_VERSION_RE.match(str(bazel_version).strip())
    return int(m.group(1)) if m else None


def load_presubmit_yml(module_name, module_version):
    with open(bcr_presubmit.get_presubmit_yml(module_name, module_version), "r") as f:
        return yaml.safe_load(f) or {}


def collect_presubmit_bazel_versions(presubmit):
    """Collect all Bazel versions referenced in a presubmit.yml (including bcr_test_module)."""
    versions = set()
    for config in (presubmit, presubmit.get("bcr_test_module")):
        if not isinstance(config, dict):
            continue
        matrix_versions = (config.get("matrix") or {}).get("bazel") or []
        if isinstance(matrix_versions, dict):
            # Matrix values can also be specified as a map from alias to value.
            matrix_versions = matrix_versions.values()
        elif not isinstance(matrix_versions, list):
            matrix_versions = [matrix_versions]
        versions.update(str(v) for v in matrix_versions)
        # "platforms" is the legacy name of "tasks".
        for task_config in (config.get("tasks") or config.get("platforms") or {}).values():
            if isinstance(task_config, dict) and task_config.get("bazel"):
                versions.add(str(task_config["bazel"]))
    # Drop matrix placeholders such as "${{ bazel }}".
    return {v for v in versions if not v.startswith("$")}


def get_target_bazel_major_versions(target_modules):
    """Return the Bazel major versions tested by each target module's presubmit.yml.

    Returns a dict mapping "<name>@<version>" to (majors, tests_newest), where `majors` are the
    major versions of the pinned Bazel versions (e.g. {8, 9} for "8.x" and "9.*"), and
    `tests_newest` tells whether the target is also tested with a symbolic version (e.g. "rolling",
    "last_green") tracking the newest Bazel, in which case any major version newer than the
    highest pinned one is considered tested too. Target modules without any pinned Bazel version
    don't restrict downstream tasks and are omitted.
    """
    requirements = {}
    for module_name, module_version in target_modules:
        target = f"{module_name}@{module_version}"
        versions = collect_presubmit_bazel_versions(load_presubmit_yml(module_name, module_version))
        majors = {get_bazel_major_version(v) for v in versions} - {None}
        symbolic_versions = sorted(v for v in versions if get_bazel_major_version(v) is None)
        if not majors:
            bazelci.eprint(
                f"* Not filtering downstream tasks by Bazel version for {target}: no pinned Bazel "
                f"version in its presubmit.yml (found {symbolic_versions})"
            )
            continue
        message = f"* {target} is tested with Bazel major versions {sorted(majors)}"
        if symbolic_versions:
            message += f" and {', '.join(symbolic_versions)}, newer major versions are also allowed"
        bazelci.eprint(message)
        requirements[target] = (majors, bool(symbolic_versions))
    return requirements


def is_bazel_major_version_tested(major, tested_majors, tests_newest):
    return major in tested_majors or (tests_newest and major > max(tested_majors))


def filter_tasks_by_bazel_major_versions(
    module_name, module_version, task_configs, target_bazel_major_versions
):
    """Drop tasks whose Bazel major version is not tested by all target modules."""
    if not target_bazel_major_versions:
        return task_configs
    filtered = {}
    for task_id, task_config in task_configs.items():
        bazel_version = task_config.get("bazel")
        major = get_bazel_major_version(bazel_version) if bazel_version else None
        # Keep tasks whose major version can't be determined statically (e.g. "latest", "rolling").
        untested_by = [
            target
            for target, (majors, tests_newest) in target_bazel_major_versions.items()
            if major is not None and not is_bazel_major_version_tested(major, majors, tests_newest)
        ]
        if untested_by:
            bazelci.eprint(
                f"* Skipping {module_name}@{module_version} task {task_id!r}: Bazel {bazel_version} "
                f"is not tested by {', '.join(untested_by)}"
            )
            continue
        filtered[task_id] = task_config
    return filtered


def parse_override_modules(override_modules_str):
    """Parse a comma-separated list of name@version pairs and validate identifiers."""
    if not override_modules_str:
        return []
    modules = []
    for item in override_modules_str.split(","):
        item = item.strip()
        if not item:
            continue
        if "@" not in item:
            bcr_presubmit.error(f"Invalid module specification (expected name@version): {item!r}")
        name, version = item.split("@", 1)
        if not bcr_presubmit.is_valid_module_identifier(name, version):
            bcr_presubmit.error(
                f"Invalid module name or version: module_name={name!r} module_version={version!r}"
            )
        modules.append((name, version))
    return modules


def select_module_versions(selections, random_percentage=None):
    """Resolve module selection patterns (e.g. "grpc@latest") using ./tools/module_selector.py."""
    args = [f"--select={s}" for s in selections]
    if random_percentage:
        args.append(f"--random-percentage={random_percentage}")
    output = subprocess.check_output(
        ["python3", "./tools/module_selector.py"] + args,
        cwd=bcr_presubmit.BCR_REPO_DIR,
    )
    modules = []
    for line in output.decode("utf-8").split():
        name, version = line.strip().split("@", 1)
        if not bcr_presubmit.is_valid_module_identifier(name, version):
            bcr_presubmit.error(
                f"Invalid module name or version from module_selector: {name}@{version}"
            )
        modules.append((name, version))
    return sorted(set(modules))


def select_target_modules_from_env():
    """Resolve TARGET_MODULES env var using ./tools/module_selector.py."""
    target_modules_env = os.environ.get("TARGET_MODULES", "").strip()
    if not target_modules_env:
        return []
    return select_module_versions([s.strip() for s in target_modules_env.split(",") if s.strip()])


def get_target_modules():
    """Return target (module_name, module_version) pairs to test downstream dependents for."""
    if os.environ.get("TARGET_MODULES", "").strip():
        return select_target_modules_from_env()
    return bcr_presubmit.get_target_modules()


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


# Options of the downstream test as {name: (default, parser)}. A target module can set them in its
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
    """Return the downstream test options for a target module."""
    target = f"{module_name}@{module_version}"
    config = load_presubmit_yml(module_name, module_version).get(DOWNSTREAM_TEST_CONFIG_KEY) or {}
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
    bazelci.eprint(f"* Downstream test options for {target}: {customized or 'defaults'}")
    return options


def get_downstream_bazel_version(target_options):
    """Return the Bazel version to override all downstream tasks with, if any."""
    targets_by_version = {}
    for (module_name, module_version), options in target_options.items():
        if options["use_bazel_version"]:
            targets_by_version.setdefault(options["use_bazel_version"], []).append(
                f"{module_name}@{module_version}"
            )
    if len(targets_by_version) > 1:
        bcr_presubmit.error(
            "Target modules set conflicting `use_bazel_version` values: "
            + "; ".join(f"{v} ({', '.join(t)})" for v, t in sorted(targets_by_version.items()))
            + ". Please set the USE_BAZEL_VERSION environment variable to choose one."
        )
    return next(iter(targets_by_version), None)


def get_top_dependents(module_names, top_n, exclude_dev_deps):
    """Return the top N direct dependents of the given modules ranked by BCR PageRank."""
    # Remove USE_BAZEL_VERSION to make this step more stable.
    env = os.environ.copy()
    env.pop("USE_BAZEL_VERSION", None)
    cmd = ["bazel", "run", "//tools:module_analyzer", "--", "--name-only", f"--top_n={top_n}"]
    if exclude_dev_deps:
        cmd.append("--exclude-dev-deps")
    cmd += [f"--dependents_of={name}" for name in module_names]
    output = subprocess.check_output(cmd, cwd=bcr_presubmit.BCR_REPO_DIR, env=env)
    return output.decode("utf-8").split()


def select_downstream_modules(target_modules, target_options):
    """Return the downstream module versions to test against the target modules.

    Downstream modules are selected for each target module according to its options (target
    modules with the same selection options are handled together), and are then tested against
    all target modules.
    """
    groups = {}
    for module_name, module_version in target_modules:
        options = target_options[(module_name, module_version)]
        selections = options["module_selections"]
        # select_top_bcr_modules and exclude_dev_deps are not used if module_selections is set.
        group = (
            selections,
            None if selections else options["select_top_bcr_modules"],
            None if selections else options["exclude_dev_deps"],
            options["smoke_test_percentage"],
        )
        groups.setdefault(group, []).append(module_name)

    target_names = {name for name, _ in target_modules}
    modules = set()
    for (selections, top_n, exclude_dev_deps, smoke_test_percentage), names in groups.items():
        if not selections and top_n:
            dependents = get_top_dependents(names, top_n, exclude_dev_deps)
            # Skip target modules in other groups, they're tested by their own presubmit.
            selections = [f"{m}@latest" for m in dependents if m not in target_names]
        if selections:
            modules.update(select_module_versions(selections, smoke_test_percentage))

    modules = sorted(modules)
    if modules:
        bazelci.print_expanded_group(
            "The following downstream modules are selected:\n\n%s"
            % "\n".join([f"{name}@{version}" for name, version in modules])
        )
    return modules


def get_vendor_bazel_version(bazel_version):
    """Return the Bazel version used to vendor the target module(s) for a task.

    Use the task's own Bazel version so that the module graph is resolved the same way as in the
    downstream build, but at least Bazel 7 since `bazel vendor` doesn't exist in older versions.
    """
    bazel_version = bazel_version or "latest"
    major = get_bazel_major_version(bazel_version)
    if major is not None and major < MIN_VENDOR_BAZEL_MAJOR_VERSION:
        return f"{MIN_VENDOR_BAZEL_MAJOR_VERSION}.x"
    return bazel_version


def vendor_target_modules(override_modules, bazel_version=None, root=None):
    """Vendor the sources of the target module(s) using `bazel vendor` and return {module_name: vendored_path}."""
    bazelci.print_collapsed_group(":package: Vendoring target modules for override")
    if not root:
        root = pathlib.Path(bazelci.get_repositories_root())
    root = pathlib.Path(root)
    root.mkdir(exist_ok=True, parents=True)

    temp_anonymous_root = root.joinpath(".temp_vendor_target_modules")
    shutil.rmtree(temp_anonymous_root, ignore_errors=True)
    temp_anonymous_root.mkdir(exist_ok=True, parents=True)

    bcr_presubmit.scratch_file(temp_anonymous_root, "WORKSPACE")
    bcr_presubmit.scratch_file(temp_anonymous_root, "BUILD")
    bcr_presubmit.scratch_file(
        temp_anonymous_root,
        "MODULE.bazel",
        [f"bazel_dep(name = '{name}', version = '{version}')" for name, version in override_modules],
    )
    bcr_presubmit.scratch_file(
        temp_anonymous_root,
        ".bazelrc",
        [
            "common --enable_bzlmod",
            "common --registry=%s" % bcr_presubmit.BCR_REPO_DIR.as_uri(),
        ],
    )

    vendor_bazel_version = get_vendor_bazel_version(bazel_version)
    bazelci.eprint(
        "* Vendoring target modules (%s) with Bazel %s"
        % (", ".join(f"{n}@{v}" for n, v in override_modules), vendor_bazel_version)
    )

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
        ]
        + [f"--repo=@{name}" for name, _ in override_modules],
        cwd=temp_anonymous_root,
        env={**os.environ, "USE_BAZEL_VERSION": vendor_bazel_version},
    )

    vendored_targets_dir = root.joinpath("vendored_target_modules")
    shutil.rmtree(vendored_targets_dir, ignore_errors=True)
    vendored_targets_dir.mkdir(exist_ok=True, parents=True)

    vendored_paths = {}
    vendor_src_dir = temp_anonymous_root.joinpath("vendor_src")
    for name, _ in override_modules:
        # The canonical repo name is "<name>+", except for well-known modules such as "platforms".
        candidates = [vendor_src_dir.joinpath(d) for d in (f"{name}+", name)]
        src_dir = next((d for d in candidates if d.is_dir()), None)
        if not src_dir:
            bcr_presubmit.error(f"Cannot find the vendored source of {name} in {vendor_src_dir}")
        dest_dir = vendored_targets_dir.joinpath(name)
        shutil.move(src_dir, dest_dir)
        vendored_paths[name] = dest_dir.resolve()
        bazelci.eprint(f"* Vendored {name} to {vendored_paths[name]}")

    return vendored_paths


def configure_downstream_override(repo_location, vendored_paths):
    """Append --override_module and dependency flags to the downstream module's .bazelrc."""
    lines = [
        "",
        "# Override target module(s) with vendored sources for downstream testing",
        "common --check_direct_dependencies=warning",
        "common --lockfile_mode=update",
    ]
    for module_name, vendored_path in vendored_paths.items():
        # Use POSIX path separators so backslashes are not treated as escapes on Windows.
        lines.append(f"common --override_module={module_name}={vendored_path.as_posix()}")

    bcr_presubmit.scratch_file(repo_location, ".bazelrc", lines, mode="a")
    bazelci.eprint(
        "* Appended downstream override flags to .bazelrc:\n%s\n"
        % "\n".join(lines[1:])
    )


def add_downstream_jobs(
    module_name,
    module_version,
    override_modules,
    task_configs,
    pipeline_steps,
    is_test_module=False,
    overwrite_bazel_version=None,
    low_priority=False,
):
    override_modules_arg = ",".join(f"{n}@{v}" for n, v in override_modules)
    override_label_str = ", ".join(f"{n}@{v}" for n, v in override_modules)

    for task_id, task_config in task_configs.items():
        platform_name = bcr_presubmit.get_platform(task_id, task_config)
        platform_label = bazelci.PLATFORMS[platform_name]["emoji-name"]
        task_name = task_config.get("name", "")
        # Keep `{module_name}@{module_version}` as the first `name@version` token so
        # generate_report.py attributes failures to the downstream module.
        label = (
            f"{module_name}@{module_version} (with {override_label_str}) - "
            f"{platform_label} - {task_name}"
        )
        bazel_version = task_config.get("bazel", "")
        if bazel_version and not overwrite_bazel_version:
            label = f":bazel:{bazel_version} - {label}"

        command = (
            '%s bcr_downstream.py %s --module_name="%s" --module_version="%s" '
            '--override_modules="%s" --task=%s %s'
            % (
                bazelci.PLATFORMS[platform_name]["python"],
                "test_module_runner" if is_test_module else "anonymous_module_runner",
                module_name,
                module_version,
                override_modules_arg,
                task_id,
                '--overwrite_bazel_version="%s"' % overwrite_bazel_version
                if overwrite_bazel_version
                else "",
            )
        )
        commands = [
            bazelci.fetch_ci_scripts_command(),
            bcr_presubmit.fetch_bcr_presubmit_py_command(),
            fetch_bcr_downstream_py_command(),
            command,
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

        priority = -100 if low_priority else -50
        pipeline_steps.append(
            bazelci.create_step(
                label,
                commands,
                platform_name,
                concurrency=concurrency,
                concurrency_group=concurrency_group,
                priority=priority,
            )
        )


def create_step_for_generate_report():
    parts = [
        bazelci.PLATFORMS[bazelci.DEFAULT_PLATFORM]["python"],
        "generate_report.py",
        "--build_number=%s" % os.getenv("BUILDKITE_BUILD_NUMBER"),
    ]
    return [
        {"wait": "~", "continue_on_failure": "true"},
        bazelci.create_step(
            label="Generate report in markdown",
            commands=[
                bazelci.fetch_ci_scripts_command(),
                bcr_presubmit.fetch_bcr_presubmit_py_command(),
                fetch_generate_report_py_command(),
                " ".join(parts),
            ],
            platform=bazelci.DEFAULT_PLATFORM,
        ),
    ]


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Bazel Central Registry Downstream Test Generator & Runner"
    )
    subparsers = parser.add_subparsers(dest="subparsers_name")

    subparsers.add_parser("bcr_downstream")

    anonymous_module_runner = subparsers.add_parser("anonymous_module_runner")
    anonymous_module_runner.add_argument("--module_name", type=str, required=True)
    anonymous_module_runner.add_argument("--module_version", type=str, required=True)
    anonymous_module_runner.add_argument("--override_modules", type=str, required=True)
    anonymous_module_runner.add_argument("--overwrite_bazel_version", type=str)
    anonymous_module_runner.add_argument("--task", type=str, required=True)

    test_module_runner = subparsers.add_parser("test_module_runner")
    test_module_runner.add_argument("--module_name", type=str, required=True)
    test_module_runner.add_argument("--module_version", type=str, required=True)
    test_module_runner.add_argument("--override_modules", type=str, required=True)
    test_module_runner.add_argument("--overwrite_bazel_version", type=str)
    test_module_runner.add_argument("--task", type=str, required=True)

    args = parser.parse_args(argv)

    if args.subparsers_name == "bcr_downstream":
        target_modules = get_target_modules()
        if not target_modules:
            bazelci.eprint("No target module versions detected for downstream testing.")
            return 0

        bazelci.print_expanded_group(
            "Target modules for downstream testing:\n\n"
            + "\n".join(f"- {name}@{version}" for name, version in target_modules)
        )

        target_options = {target: get_downstream_test_options(*target) for target in target_modules}
        # Override the Bazel versions in the downstream presubmit.yml files if USE_BAZEL_VERSION
        # (or `use_bazel_version` in the target modules' presubmit.yml) is specified.
        bazel_version = get_downstream_bazel_version(target_options)

        downstream_modules = select_downstream_modules(target_modules, target_options)
        if not downstream_modules:
            bazelci.eprint("No downstream modules selected for the target module(s).")
            return 0

        pr_labels = bcr_presubmit.get_labels_from_pr()
        low_priority = "low-ci-priority" in pr_labels
        # Skip downstream tasks with Bazel major versions not tested by the target module(s).
        target_bazel_major_versions = get_target_bazel_major_versions(target_modules)

        pipeline_steps = []
        for downstream_name, downstream_version in downstream_modules:
            configs = bcr_presubmit.get_anonymous_module_task_config(
                downstream_name, downstream_version, bazel_version
            )
            add_downstream_jobs(
                downstream_name,
                downstream_version,
                target_modules,
                filter_tasks_by_bazel_major_versions(
                    downstream_name,
                    downstream_version,
                    configs.get("tasks", {}),
                    target_bazel_major_versions,
                ),
                pipeline_steps,
                overwrite_bazel_version=bazel_version,
                low_priority=low_priority,
            )
            configs = bcr_presubmit.get_test_module_task_config(
                downstream_name, downstream_version, bazel_version
            )
            add_downstream_jobs(
                downstream_name,
                downstream_version,
                target_modules,
                filter_tasks_by_bazel_major_versions(
                    downstream_name,
                    downstream_version,
                    configs.get("tasks", {}),
                    target_bazel_major_versions,
                ),
                pipeline_steps,
                is_test_module=True,
                overwrite_bazel_version=bazel_version,
                low_priority=low_priority,
            )

        if pipeline_steps:
            if (
                "SKIP_WAIT_FOR_APPROVAL" not in os.environ
                and "run-downstream-test" not in pr_labels
                and bcr_presubmit.should_wait_bcr_maintainer_review(target_modules, pr_labels)
            ):
                pipeline_steps.insert(
                    0,
                    {"block": "Wait on BCR maintainer review", "blocked_state": "running"},
                )
            pipeline_steps += create_step_for_generate_report()

        bcr_presubmit.upload_jobs_to_pipeline(pipeline_steps)
    elif args.subparsers_name == "anonymous_module_runner":
        if not bcr_presubmit.is_valid_module_identifier(args.module_name, args.module_version):
            bcr_presubmit.error(
                f"Invalid downstream module identifier: {args.module_name}@{args.module_version}"
            )
        override_modules = parse_override_modules(args.override_modules)
        config_file = bcr_presubmit.get_presubmit_yml(args.module_name, args.module_version)
        # Vendor the target module(s) with the same Bazel version as the task, so that
        # the target module is fetched with a Bazel version it supports.
        task_bazel_version = bcr_presubmit.get_bazel_version_for_task(
            config_file, args.task, args.overwrite_bazel_version
        )
        vendored_paths = vendor_target_modules(override_modules, bazel_version=task_bazel_version)
        repo_location = bcr_presubmit.create_anonymous_repo(args.module_name, args.module_version)
        configure_downstream_override(repo_location, vendored_paths)
        return bcr_presubmit.run_test(
            repo_location, config_file, args.task, args.overwrite_bazel_version
        )
    elif args.subparsers_name == "test_module_runner":
        if not bcr_presubmit.is_valid_module_identifier(args.module_name, args.module_version):
            bcr_presubmit.error(
                f"Invalid downstream module identifier: {args.module_name}@{args.module_version}"
            )
        override_modules = parse_override_modules(args.override_modules)
        repo_location, config_file = bcr_presubmit.prepare_test_module_repo(
            args.module_name, args.module_version, args.overwrite_bazel_version
        )
        task_bazel_version = bcr_presubmit.get_bazel_version_for_task(
            config_file, args.task, args.overwrite_bazel_version
        )
        vendored_paths = vendor_target_modules(override_modules, bazel_version=task_bazel_version)
        configure_downstream_override(repo_location, vendored_paths)
        return bcr_presubmit.run_test(
            repo_location, config_file, args.task, args.overwrite_bazel_version
        )
    else:
        parser.print_help()
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
