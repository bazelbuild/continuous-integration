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
import ast
import json
import os
import pathlib
import re
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
DEFAULT_MAX_DOWNSTREAM_MODULES = 10

BAZEL_DEP_NAME_RE = re.compile(
    r"""bazel_dep\s*\([^)]*?\bname\s*=\s*["']([^"']+)["']""", re.DOTALL
)


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


def extract_direct_deps_from_module_bazel(module_bazel_path, exclude_dev_deps=False):
    """Extract direct bazel_dep module names from a MODULE.bazel file."""
    content = module_bazel_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(content, filename=str(module_bazel_path))
        deps = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "bazel_dep":
                dep_name = None
                is_dev_dep = False
                for kw in node.keywords:
                    if kw.arg == "name" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        dep_name = kw.value.value
                    elif kw.arg == "dev_dependency" and isinstance(kw.value, ast.Constant):
                        is_dev_dep = bool(kw.value.value)
                if dep_name and not (exclude_dev_deps and is_dev_dep):
                    deps.append(dep_name)
        return deps
    except SyntaxError:
        # Fallback to regex if MODULE.bazel contains constructs rejected by Python's ast.
        return BAZEL_DEP_NAME_RE.findall(content)


def get_latest_non_yanked_version(module_name):
    """Return the latest non-yanked version of a module from its metadata.json."""
    metadata_path = bcr_presubmit.get_metadata_json(module_name)
    if not metadata_path.exists():
        return None
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    versions = metadata.get("versions", [])
    yanked = metadata.get("yanked_versions", {})
    non_yanked = [v for v in versions if v not in yanked]
    if non_yanked:
        return non_yanked[-1]
    return versions[-1] if versions else None


def build_bcr_dependency_graph(exclude_dev_deps=False):
    """Build the latest-version dependency graph across all BCR modules.

    Returns:
        latest_versions: dict mapping module_name -> latest_non_yanked_version
        edges: dict mapping module_name -> list of direct dependency module_names in BCR
    """
    modules_dir = bcr_presubmit.BCR_REPO_DIR.joinpath("modules")
    latest_versions = {}

    for module_dir in sorted(modules_dir.iterdir()):
        if not module_dir.is_dir():
            continue
        module_name = module_dir.name
        if not bcr_presubmit.MODULE_NAME_RE.match(module_name):
            continue
        latest_version = get_latest_non_yanked_version(module_name)
        if not latest_version or not bcr_presubmit.is_valid_module_identifier(
            module_name, latest_version
        ):
            continue
        latest_versions[module_name] = latest_version

    edges = {name: [] for name in latest_versions}
    for module_name, latest_version in latest_versions.items():
        module_bazel_path = bcr_presubmit.get_module_dot_bazel(module_name, latest_version)
        if not module_bazel_path.exists():
            continue
        direct_deps = extract_direct_deps_from_module_bazel(
            module_bazel_path, exclude_dev_deps=exclude_dev_deps
        )
        # Preserve unique edges to modules present in the registry (matching nx.DiGraph in module_analyzer.py)
        edges[module_name] = sorted(
            {dep for dep in direct_deps if dep in latest_versions and dep != module_name}
        )

    return latest_versions, edges


def compute_pagerank(edges, alpha=0.85, max_iter=100, tol=1.0e-6):
    """Compute PageRank scores over the directed graph `edges` (matching networkx.pagerank)."""
    nodes = sorted(edges.keys())
    n = len(nodes)
    if n == 0:
        return {}

    pr = {node: 1.0 / n for node in nodes}
    dangling_nodes = [node for node in nodes if not edges[node]]

    for _ in range(max_iter):
        next_pr = {node: (1.0 - alpha) / n for node in nodes}
        dangling_sum = sum(pr[node] for node in dangling_nodes)
        dangling_contrib = alpha * dangling_sum / n

        for node in nodes:
            next_pr[node] += dangling_contrib
            out_neighbors = edges[node]
            if out_neighbors:
                share = alpha * pr[node] / len(out_neighbors)
                for dst in out_neighbors:
                    next_pr[dst] += share

        err = sum(abs(next_pr[node] - pr[node]) for node in nodes)
        pr = next_pr
        if err < n * tol:
            break

    return pr


def select_downstream_modules(target_modules, max_downstream_modules=None, exclude_dev_deps=False):
    """Discover direct downstream modules and select the top N by PageRank."""
    if max_downstream_modules is None:
        max_downstream_modules = int(
            os.environ.get("MAX_DOWNSTREAM_MODULES", DEFAULT_MAX_DOWNSTREAM_MODULES)
        )

    latest_versions, edges = build_bcr_dependency_graph(exclude_dev_deps=exclude_dev_deps)
    target_names_set = {name for name, _ in target_modules}

    direct_dependents = {
        module_name: latest_versions[module_name]
        for module_name, deps in edges.items()
        if module_name not in target_names_set and target_names_set.intersection(deps)
    }
    if not direct_dependents:
        return []

    pagerank = compute_pagerank(edges)
    pagerank_order = sorted(pagerank.keys(), key=lambda m: (-pagerank[m], m))
    rank_index = {name: idx for idx, name in enumerate(pagerank_order)}

    sorted_dependent_names = sorted(
        direct_dependents.keys(),
        key=lambda name: (-pagerank.get(name, 0.0), name),
    )

    selected_names = sorted_dependent_names[:max_downstream_modules]
    selected = [(name, direct_dependents[name]) for name in selected_names]

    bazelci.print_expanded_group(
        f"Selected {len(selected)} of {len(direct_dependents)} direct downstream modules (top {max_downstream_modules} by PageRank):\n\n"
        + "\n".join(
            f"{idx + 1}. {name}@{version} (PageRank: {pagerank.get(name, 0.0):.6f}, global rank #{rank_index.get(name, -1) + 1})"
            for idx, (name, version) in enumerate(selected)
        )
    )
    return selected


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
        bazel_version = overwrite_bazel_version or task_config.get("bazel", "")
        if bazel_version:
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

        exclude_dev_deps = os.environ.get("EXCLUDE_DEV_DEPS", "").lower() in ("1", "true", "yes")
        downstream_modules = select_downstream_modules(
            target_modules, exclude_dev_deps=exclude_dev_deps
        )
        if not downstream_modules:
            bazelci.eprint("No direct downstream modules found in BCR for the target module(s).")
            return 0

        pr_labels = bcr_presubmit.get_labels_from_pr()
        low_priority = "low-ci-priority" in pr_labels
        # Default to "latest" Bazel unless USE_BAZEL_VERSION is explicitly set (or set to "" to test all matrix versions).
        bazel_version = os.environ.get("USE_BAZEL_VERSION", "latest") or None

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
