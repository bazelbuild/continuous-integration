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
import shutil
import subprocess
import sys
import time

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


def fetch_bcr_downstream_py_command():
    return bazelci.curl_download_command(SCRIPT_URL, "bcr_downstream.py")


def fetch_generate_report_py_command():
    return bazelci.curl_download_command(GENERATE_REPORT_URL, "generate_report.py")


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


def select_target_modules_from_env():
    """Resolve TARGET_MODULES env var using ./tools/module_selector.py."""
    target_modules_env = os.environ.get("TARGET_MODULES", "").strip()
    if not target_modules_env:
        return []

    selections = [s.strip() for s in target_modules_env.split(",") if s.strip()]
    args = [f"--select={s}" for s in selections]
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


def get_target_modules():
    """Return target (module_name, module_version) pairs to test downstream dependents for."""
    if os.environ.get("TARGET_MODULES", "").strip():
        return select_target_modules_from_env()
    return bcr_presubmit.get_target_modules()


def select_downstream_modules(target_modules):
    """
    Parses MODULE_SELECTIONS, SELECT_TOP_BCR_MODULES, and SMOKE_TEST_PERCENTAGE
    environment variables and returns a list of selected downstream module versions.
    """
    MODULE_SELECTIONS = os.environ.get("MODULE_SELECTIONS", "")
    SMOKE_TEST_PERCENTAGE = os.environ.get("SMOKE_TEST_PERCENTAGE", None)

    top_n = os.environ.get("SELECT_TOP_BCR_MODULES", DEFAULT_TOP_BCR_MODULES)
    if top_n and not MODULE_SELECTIONS:
        # Remove USE_BAZEL_VERSION to make this step more stable.
        env = os.environ.copy()
        env.pop("USE_BAZEL_VERSION", None)
        cmd = [
            "bazel",
            "run",
            "//tools:module_analyzer",
            "--",
            "--name-only",
            f"--top_n={top_n}",
        ]
        if os.environ.get("EXCLUDE_DEV_DEPS", "").lower() in ("1", "true", "yes"):
            cmd.append("--exclude-dev-deps")
        for module_name, _ in target_modules:
            cmd.append(f"--dependents_of={module_name}")
        output = subprocess.check_output(
            cmd,
            cwd=bcr_presubmit.BCR_REPO_DIR,
            env=env,
        )
        top_modules = output.decode("utf-8").split()
        MODULE_SELECTIONS = ",".join([f"{module}@latest" for module in top_modules])

    if not MODULE_SELECTIONS:
        return []

    selections = [s.strip() for s in MODULE_SELECTIONS.split(",") if s.strip()]
    args = [f"--select={s}" for s in selections]
    if SMOKE_TEST_PERCENTAGE:
        args += [f"--random-percentage={SMOKE_TEST_PERCENTAGE}"]
    output = subprocess.check_output(
        ["python3", "./tools/module_selector.py"] + args,
        cwd=bcr_presubmit.BCR_REPO_DIR,
    )
    modules = []
    for line in output.decode("utf-8").split():
        name, version = line.strip().split("@")
        modules.append((name, version))
    if modules:
        bazelci.print_expanded_group(
            "The following downstream modules are selected:\n\n%s"
            % "\n".join([f"{name}@{version}" for name, version in modules])
        )
    return sorted(list(set(modules)))


def vendor_target_modules(override_modules, overwrite_bazel_version=None, root=None):
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

    vendor_bazel_version = overwrite_bazel_version or "latest"
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
        ]
        + [f"--repo=@{name}" for name, _ in override_modules],
        cwd=temp_anonymous_root,
        env={**os.environ, "USE_BAZEL_VERSION": vendor_bazel_version},
    )

    vendored_targets_dir = root.joinpath("vendored_target_modules")
    shutil.rmtree(vendored_targets_dir, ignore_errors=True)
    vendored_targets_dir.mkdir(exist_ok=True, parents=True)

    vendored_paths = {}
    for name, _ in override_modules:
        src_dir = temp_anonymous_root.joinpath(f"vendor_src/{name}+")
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
                "--overwrite_bazel_version=%s" % overwrite_bazel_version
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

        downstream_modules = select_downstream_modules(target_modules)
        if not downstream_modules:
            bazelci.eprint("No direct downstream modules found in BCR for the target module(s).")
            return 0

        pr_labels = bcr_presubmit.get_labels_from_pr()
        low_priority = "low-ci-priority" in pr_labels
        # Respect USE_BAZEL_VERSION to override bazel version in presubmit.yml files if specified.
        bazel_version = os.environ.get("USE_BAZEL_VERSION")

        pipeline_steps = []
        for downstream_name, downstream_version in downstream_modules:
            configs = bcr_presubmit.get_anonymous_module_task_config(
                downstream_name, downstream_version, bazel_version
            )
            add_downstream_jobs(
                downstream_name,
                downstream_version,
                target_modules,
                configs.get("tasks", {}),
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
                configs.get("tasks", {}),
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
        vendored_paths = vendor_target_modules(
            override_modules, overwrite_bazel_version=args.overwrite_bazel_version
        )
        repo_location = bcr_presubmit.create_anonymous_repo(args.module_name, args.module_version)
        configure_downstream_override(repo_location, vendored_paths)
        config_file = bcr_presubmit.get_presubmit_yml(args.module_name, args.module_version)
        return bcr_presubmit.run_test(
            repo_location, config_file, args.task, args.overwrite_bazel_version
        )
    elif args.subparsers_name == "test_module_runner":
        if not bcr_presubmit.is_valid_module_identifier(args.module_name, args.module_version):
            bcr_presubmit.error(
                f"Invalid downstream module identifier: {args.module_name}@{args.module_version}"
            )
        override_modules = parse_override_modules(args.override_modules)
        vendored_paths = vendor_target_modules(
            override_modules, overwrite_bazel_version=args.overwrite_bazel_version
        )
        repo_location, config_file = bcr_presubmit.prepare_test_module_repo(
            args.module_name, args.module_version, args.overwrite_bazel_version
        )
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
