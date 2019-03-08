#!/usr/bin/env python3
#
# Copyright 2019 The Bazel Authors. All rights reserved.
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

import base64
import tempfile
import os
import uuid
import time
import subprocess
import stat
import shutil
import multiprocessing
import re
import json
from urllib.request import url2pathname
from urllib.parse import urlparse

from config import CLOUD_PROJECT, PLATFORMS
from utils import (
    bazelci_builds_gs_url,
    create_label,
    eprint,
    execute_command,
    gcloud_command,
    gsutil_command,
    print_collapsed_group,
    print_expanded_group,
)


ENCRYPTED_SAUCELABS_TOKEN = """
CiQAry63sOlZtTNtuOT5DAOLkum0rGof+DOweppZY1aOWbat8zwSTQAL7Hu+rgHSOr6P4S1cu4YG
/I1BHsWaOANqUgFt6ip9/CUGGJ1qggsPGXPrmhSbSPqNAIAkpxYzabQ3mfSIObxeBmhKg2dlILA/
EDql
""".strip()


def saucelabs_token():
    return (
        subprocess.check_output(
            [
                gcloud_command(),
                "kms",
                "decrypt",
                "--project",
                "bazel-untrusted",
                "--location",
                "global",
                "--keyring",
                "buildkite",
                "--key",
                "saucelabs-access-key",
                "--ciphertext-file",
                "-",
                "--plaintext-file",
                "-",
            ],
            input=base64.b64decode(ENCRYPTED_SAUCELABS_TOKEN),
            env=os.environ,
        )
        .decode("utf-8")
        .strip()
    )


def downstream_projects_root(platform):
    downstream_projects_dir = os.path.expandvars(
        "${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects"
    )
    agent_directory = os.path.expandvars(PLATFORMS[platform]["agent-directory"])
    path = os.path.join(agent_directory, downstream_projects_dir)
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def clone_git_repository(git_repository, platform, git_commit=None):
    root = downstream_projects_root(platform)
    project_name = re.search(r"/([^/]+)\.git$", git_repository).group(1)
    clone_path = os.path.join(root, project_name)
    print_collapsed_group(
        "Fetching %s sources at %s" % (project_name, git_commit if git_commit else "HEAD")
    )

    if not os.path.exists(clone_path):
        if platform in ["ubuntu1404", "ubuntu1604", "ubuntu1804", "rbe_ubuntu1604"]:
            execute_command(
                ["git", "clone", "--reference", "/var/lib/bazelbuild", git_repository, clone_path]
            )
        elif platform in ["macos"]:
            execute_command(
                [
                    "git",
                    "clone",
                    "--reference",
                    "/usr/local/var/bazelbuild",
                    git_repository,
                    clone_path,
                ]
            )
        elif platform in ["windows"]:
            execute_command(
                [
                    "git",
                    "clone",
                    "--reference",
                    "c:\\buildkite\\bazelbuild",
                    git_repository,
                    clone_path,
                ]
            )
        else:
            execute_command(["git", "clone", git_repository, clone_path])

    os.chdir(clone_path)
    execute_command(["git", "remote", "set-url", "origin", git_repository])
    execute_command(["git", "clean", "-fdqx"])
    execute_command(["git", "submodule", "foreach", "--recursive", "git", "clean", "-fdqx"])
    execute_command(["git", "fetch", "origin"])
    if git_commit:
        # sync to a specific commit of this repository
        execute_command(["git", "reset", git_commit, "--hard"])
    else:
        # sync to the latest commit of HEAD. Unlikely git pull this also works after a force push.
        remote_head = (
            subprocess.check_output(["git", "symbolic-ref", "refs/remotes/origin/HEAD"])
            .decode("utf-8")
            .rstrip()
        )
        execute_command(["git", "reset", remote_head, "--hard"])
    execute_command(["git", "submodule", "sync", "--recursive"])
    execute_command(["git", "submodule", "update", "--init", "--recursive", "--force"])
    execute_command(["git", "submodule", "foreach", "--recursive", "git", "reset", "--hard"])
    execute_command(["git", "clean", "-fdqx"])
    execute_command(["git", "submodule", "foreach", "--recursive", "git", "clean", "-fdqx"])
    return clone_path


def common_startup_flags(platform):
    return ["--output_user_root=D:/b"] if platform == "windows" else []


def print_bazel_version_info(bazel_binary, platform):
    print_collapsed_group(":information_source: Bazel Info")
    execute_command(
        [bazel_binary]
        + common_startup_flags(platform)
        + ["--nomaster_bazelrc", "--bazelrc=/dev/null", "version"]
    )
    execute_command(
        [bazel_binary]
        + common_startup_flags(platform)
        + ["--nomaster_bazelrc", "--bazelrc=/dev/null", "info"]
    )


def download_bazel_binary_at_commit(dest_dir, platform, bazel_git_commit):
    # We only build bazel binary on ubuntu14.04 for every bazel commit.
    # It should be OK to use it on other ubuntu platforms.
    if "ubuntu" in PLATFORMS[platform].get("host-platform", platform):
        platform = "ubuntu1404"
    bazel_binary_path = os.path.join(dest_dir, "bazel.exe" if platform == "windows" else "bazel")
    try:
        execute_command(
            [
                gsutil_command(),
                "cp",
                bazelci_builds_gs_url(platform, bazel_git_commit),
                bazel_binary_path,
            ]
        )
    except subprocess.CalledProcessError as e:
        raise Exception(
            "Failed to download Bazel binary at %s, error message:\n%s" % (bazel_git_commit, str(e))
        )
    st = os.stat(bazel_binary_path)
    os.chmod(bazel_binary_path, st.st_mode | stat.S_IEXEC)
    return bazel_binary_path


def execute_batch_commands(commands):
    if not commands:
        return
    print_collapsed_group(":batch: Setup (Batch Commands)")
    batch_commands = "&".join(commands)
    subprocess.run(batch_commands, shell=True, check=True, env=os.environ)


def execute_shell_commands(commands):
    if not commands:
        return
    print_collapsed_group(":bash: Setup (Shell Commands)")
    shell_command = "\n".join(commands)
    execute_command([shell_command], shell=True)


def execute_bazel_run(bazel_binary, platform, targets, incompatible_flags):
    if not targets:
        return
    print_collapsed_group("Setup (Run Targets)")
    for target in targets:
        execute_command(
            [bazel_binary]
            + common_startup_flags(platform)
            + ["run"]
            + common_build_flags(None, platform)
            + (incompatible_flags or [])
            + [target]
        )


def print_environment_variables_info():
    print_collapsed_group(":information_source: Environment Variables")
    for key, value in os.environ.items():
        eprint("%s=(%s)" % (key, value))


def execute_command_background(args):
    eprint(" ".join(args))
    return subprocess.Popen(args, env=os.environ)


def execute_bazel_clean(bazel_binary, platform):
    print_expanded_group(":bazel: Clean")

    try:
        execute_command([bazel_binary] + common_startup_flags(platform) + ["clean", "--expunge"])
    except subprocess.CalledProcessError as e:
        raise Exception("bazel clean failed with exit code {}".format(e.returncode))


def concurrent_jobs(platform):
    return "75" if platform.startswith("rbe_") else str(multiprocessing.cpu_count())


def common_build_flags(bep_file, platform):
    flags = [
        "--show_progress_rate_limit=5",
        "--curses=yes",
        "--color=yes",
        "--verbose_failures",
        "--keep_going",
        "--jobs=" + concurrent_jobs(platform),
        "--announce_rc",
        "--experimental_multi_threaded_digest",
    ]

    if platform != "windows":
        flags += ["--sandbox_tmpfs_path=/tmp"]

    if bep_file:
        flags += [
            "--experimental_build_event_json_file_path_conversion=false",
            "--build_event_json_file=" + bep_file,
        ]

    return flags


def remote_enabled(flags):
    # Detect if the project configuration enabled its own remote caching / execution.
    remote_flags = ["--remote_executor", "--remote_cache", "--remote_http_cache"]
    for flag in flags:
        for remote_flag in remote_flags:
            if flag.startswith(remote_flag):
                return True
    return False


def rbe_flags(original_flags, accept_cached):
    # Enable remote execution via RBE.
    flags = [
        "--remote_executor=remotebuildexecution.googleapis.com",
        "--remote_instance_name=projects/bazel-untrusted/instances/default_instance",
        "--remote_timeout=3600",
        "--spawn_strategy=remote",
        "--strategy=Javac=remote",
        "--strategy=Closure=remote",
        "--genrule_strategy=remote",
        "--experimental_strict_action_env",
        "--tls_enabled=true",
        "--google_default_credentials",
    ]

    # Enable BES / Build Results reporting.
    flags += [
        "--bes_backend=buildeventservice.googleapis.com",
        "--bes_timeout=360s",
        "--project_id=bazel-untrusted",
    ]

    if not accept_cached:
        flags += ["--noremote_accept_cached"]

    # Copied from https://github.com/bazelbuild/bazel-toolchains/blob/master/bazelrc/.bazelrc
    flags += [
        # Toolchain related flags to append at the end of your .bazelrc file.
        "--host_javabase=@buildkite_config//java:jdk",
        "--javabase=@buildkite_config//java:jdk",
        "--host_java_toolchain=@bazel_tools//tools/jdk:toolchain_hostjdk8",
        "--java_toolchain=@bazel_tools//tools/jdk:toolchain_hostjdk8",
        "--crosstool_top=@buildkite_config//cc:toolchain",
        "--action_env=BAZEL_DO_NOT_DETECT_CPP_TOOLCHAIN=1",
    ]

    # Platform flags:
    # The toolchain container used for execution is defined in the target indicated
    # by "extra_execution_platforms", "host_platform" and "platforms".
    # Projects that use the rbe_ubuntu1604 config must have an
    # rbe_autoconfig target in their WORKSPACE with name="buildkite_config".
    # The generated @buildkite_config includes a platform that uses
    # the latest rbe-ubuntu-1604 container
    # (https://gcr.io/cloud-marketplace/google/rbe-ubuntu16-04)
    #
    # Note: If you run into issues with the rbe_ubuntu1604 config
    # (e.g., CI complains that it requires docker to run the rule)
    # update your pin to bazel-toolchains in the WORKSPACE to the latest release:
    # https://releases.bazel.build/bazel-toolchains.html
    # rbe_autoconfig docs are here:
    # https://github.com/bazelbuild/bazel-toolchains/blob/c8133890211f9e8394af3272d47065787a9735e3/rules/rbe_repo.bzl
    #
    # Note: If your build requires a custom platform (i.e., it needs custom
    # properties) or requires using a custom container you need to:
    #   1. create a platform target that has
    #      parents = ["@buildkite_config//config:platform"], and adds the
    #      {PARENT_REMOTE_EXECUTION_PROPERTIES} to remote_execution_properties.
    #      Example:
    #      https://github.com/bazelbuild/bazel-toolchains/blob/c8133890211f9e8394af3272d47065787a9735e3/configs/ubuntu16_04_clang/BUILD#L31
    #   2. Override the container in the rbe_autoconfig rule. Example:
    #      https://github.com/bazelbuild/rules_docker/blob/f40c92d1b30ff758a66aba7578039cbf959aea62/WORKSPACE#L294
    #   3. Pass flags to override the platforms defined below in your
    #      .presubmit.yaml file.
    # More about platforms: https://docs.bazel.build/versions/master/platforms.html
    # Don't add platform flags if they are specified already.
    platform_flags = {
        "--extra_toolchains": "@buildkite_config//config:cc-toolchain",
        "--extra_execution_platforms": "@buildkite_config//config:platform",
        "--host_platform": "@buildkite_config//config:platform",
        "--platforms": "@buildkite_config//config:platform",
    }
    for platform_flag, value in list(platform_flags.items()):
        found = False
        for original_flag in original_flags:
            if original_flag.startswith(platform_flag):
                found = True
                break
        if not found:
            flags += [platform_flag + "=" + value]

    return flags


def concurrent_test_jobs(platform):
    if platform.startswith("rbe_"):
        return "75"
    if platform == "windows":
        return "8"
    if platform == "macos":
        return "8"
    return "12"


def remote_caching_flags(platform):
    if platform not in [
        "ubuntu1404",
        "ubuntu1604",
        "ubuntu1804",
        "ubuntu1804_nojava",
        "ubuntu1804_java9",
        "ubuntu1804_java10",
        "ubuntu1804_java11",
        "macos",
        # "windows",
    ]:
        return []

    flags = [
        "--remote_timeout=60",
        "--disk_cache=",
        "--remote_max_connections=200",
        '--host_platform_remote_properties_override=properties:{name:"platform" value:"%s"}'
        % platform,
    ]

    if platform == "macos":
        if CLOUD_PROJECT == "bazel-public":
            # Use a local trusted cache server for our macOS machines.
            flags += ["--remote_http_cache=http://100.107.67.248:8081"]
        else:
            # Use a local untrusted cache server for our macOS machines.
            flags += ["--remote_http_cache=http://100.107.67.248:8080"]
    else:
        flags += ["--google_default_credentials"]
        if CLOUD_PROJECT == "bazel-public":
            flags += [
                "--remote_http_cache=https://storage.googleapis.com/bazel-trusted-buildkite-cache"
            ]
        else:
            flags += [
                "--remote_http_cache=https://storage.googleapis.com/bazel-untrusted-buildkite-cache"
            ]

    return flags


def compute_flags(platform, flags, incompatible_flags, bep_file, enable_remote_cache=False):
    aggregated_flags = common_build_flags(bep_file, platform)
    if not remote_enabled(flags):
        if platform.startswith("rbe_"):
            aggregated_flags += rbe_flags(flags, accept_cached=enable_remote_cache)
        elif enable_remote_cache:
            aggregated_flags += remote_caching_flags(platform)
    aggregated_flags += flags
    if incompatible_flags:
        aggregated_flags += incompatible_flags

    return aggregated_flags


def execute_bazel_build(bazel_binary, platform, flags, targets, bep_file, incompatible_flags):
    print_expanded_group(":bazel: Build")

    aggregated_flags = compute_flags(
        platform, flags, incompatible_flags, bep_file, enable_remote_cache=True
    )
    try:
        execute_command(
            [bazel_binary] + common_startup_flags(platform) + ["build"] + aggregated_flags + targets
        )
    except subprocess.CalledProcessError as e:
        raise Exception("bazel build failed with exit code {}".format(e.returncode))


def execute_bazel_test(
    bazel_binary, platform, flags, targets, bep_file, monitor_flaky_tests, incompatible_flags
):
    print_expanded_group(":bazel: Test")

    aggregated_flags = [
        "--flaky_test_attempts=3",
        "--build_tests_only",
        "--local_test_jobs=" + concurrent_test_jobs(platform),
    ]
    # Don't enable remote caching if the user enabled remote execution / caching themselves
    # or flaky test monitoring is enabled, as remote caching makes tests look less flaky than
    # they are.
    aggregated_flags += compute_flags(
        platform, flags, incompatible_flags, bep_file, enable_remote_cache=not monitor_flaky_tests
    )

    try:
        execute_command(
            [bazel_binary] + common_startup_flags(platform) + ["test"] + aggregated_flags + targets
        )
    except subprocess.CalledProcessError as e:
        raise Exception("bazel test failed with exit code {}".format(e.returncode))


def upload_bazel_binary(platform):
    print_collapsed_group(":gcloud: Uploading Bazel Under Test")
    binary_path = "bazel-bin/src/bazel"
    if platform == "windows":
        binary_path = r"bazel-bin\src\bazel"
    execute_command(["buildkite-agent", "artifact", "upload", binary_path])


def test_logs_for_status(bep_file, status):
    targets = []
    raw_data = ""
    with open(bep_file, encoding="utf-8") as f:
        raw_data = f.read()
    decoder = json.JSONDecoder()

    pos = 0
    while pos < len(raw_data):
        bep_obj, size = decoder.raw_decode(raw_data[pos:])
        if "testSummary" in bep_obj:
            test_target = bep_obj["id"]["testSummary"]["label"]
            test_status = bep_obj["testSummary"]["overallStatus"]
            if test_status == status:
                outputs = bep_obj["testSummary"]["failed"]
                test_logs = []
                for output in outputs:
                    test_logs.append(url2pathname(urlparse(output["uri"]).path))
                targets.append((test_target, test_logs))
        pos += size + 1
    return targets


def has_flaky_tests(bep_file):
    return len(test_logs_for_status(bep_file, status="FLAKY")) > 0


def test_label_to_path(tmpdir, label, attempt):
    # remove leading //
    path = label[2:]
    path = path.replace("/", os.sep)
    path = path.replace(":", os.sep)
    if attempt == 0:
        path = os.path.join(path, "test.log")
    else:
        path = os.path.join(path, "attempt_" + str(attempt) + ".log")
    return os.path.join(tmpdir, path)


def test_logs_to_upload(bep_file, tmpdir):
    failed = test_logs_for_status(bep_file, status="FAILED")
    timed_out = test_logs_for_status(bep_file, status="TIMEOUT")
    flaky = test_logs_for_status(bep_file, status="FLAKY")
    # Rename the test.log files to the target that created them
    # so that it's easy to associate test.log and target.
    new_paths = []
    for label, test_logs in failed + timed_out + flaky:
        attempt = 0
        if len(test_logs) > 1:
            attempt = 1
        for test_log in test_logs:
            try:
                new_path = test_label_to_path(tmpdir, label, attempt)
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                shutil.copyfile(test_log, new_path)
                new_paths.append(new_path)
                attempt += 1
            except IOError as err:
                # Log error and ignore.
                eprint(err)
    return new_paths


def upload_test_logs(bep_file, tmpdir):
    if not os.path.exists(bep_file):
        return
    test_logs = test_logs_to_upload(bep_file, tmpdir)
    if test_logs:
        cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            test_logs = [os.path.relpath(test_log, tmpdir) for test_log in test_logs]
            test_logs = sorted(test_logs)
            print_collapsed_group(":gcloud: Uploading Test Logs")
            execute_command(["buildkite-agent", "artifact", "upload", ";".join(test_logs)])
        finally:
            os.chdir(cwd)


def download_bazel_binary(dest_dir, platform):
    host_platform = PLATFORMS[platform].get("host-platform", platform)
    binary_path = "bazel-bin/src/bazel"
    if platform == "windows":
        binary_path = r"bazel-bin\src\bazel"

    source_step = create_label(host_platform, "Bazel", build_only=True)
    execute_command(
        ["buildkite-agent", "artifact", "download", binary_path, dest_dir, "--step", source_step]
    )
    bazel_binary_path = os.path.join(dest_dir, binary_path)
    st = os.stat(bazel_binary_path)
    os.chmod(bazel_binary_path, st.st_mode | stat.S_IEXEC)
    return bazel_binary_path


def main(
    config,
    platform,
    git_repository,
    git_commit,
    git_repo_location,
    use_bazel_at_commit,
    use_but,
    save_but,
    needs_clean,
    build_only,
    test_only,
    monitor_flaky_tests,
    incompatible_flags,
):
    build_only = build_only or "test_targets" not in config
    test_only = test_only or "build_targets" not in config
    if build_only and test_only:
        raise Exception("build_only and test_only cannot be true at the same time")

    if use_bazel_at_commit and use_but:
        raise Exception("use_bazel_at_commit cannot be set when use_but is true")

    tmpdir = tempfile.mkdtemp()
    sc_process = None
    try:
        if git_repo_location:
            os.chdir(git_repo_location)
        elif git_repository:
            clone_git_repository(git_repository, platform, git_commit)
        else:
            git_repository = os.getenv("BUILDKITE_REPO")

        if use_bazel_at_commit:
            print_collapsed_group(":gcloud: Downloading Bazel built at " + use_bazel_at_commit)
            bazel_binary = download_bazel_binary_at_commit(tmpdir, platform, use_bazel_at_commit)
        elif use_but:
            print_collapsed_group(":gcloud: Downloading Bazel Under Test")
            bazel_binary = download_bazel_binary(tmpdir, platform)
        else:
            bazel_binary = "bazel"

        print_bazel_version_info(bazel_binary, platform)

        print_environment_variables_info()

        if incompatible_flags:
            print_expanded_group("Build and test with the following incompatible flags:")
            for flag in incompatible_flags:
                eprint(flag + "\n")

        if platform == "windows":
            execute_batch_commands(config.get("batch_commands", None))
        else:
            execute_shell_commands(config.get("shell_commands", None))
        execute_bazel_run(
            bazel_binary, platform, config.get("run_targets", None), incompatible_flags
        )

        if config.get("sauce", None):
            print_collapsed_group(":saucelabs: Starting Sauce Connect Proxy")
            os.environ["SAUCE_USERNAME"] = "bazel_rules_webtesting"
            os.environ["SAUCE_ACCESS_KEY"] = saucelabs_token()
            os.environ["TUNNEL_IDENTIFIER"] = str(uuid.uuid4())
            os.environ["BUILD_TAG"] = str(uuid.uuid4())
            readyfile = os.path.join(tmpdir, "sc_is_ready")
            if platform == "windows":
                cmd = ["sauce-connect.exe", "/i", os.environ["TUNNEL_IDENTIFIER"], "/f", readyfile]
            else:
                cmd = ["sc", "-i", os.environ["TUNNEL_IDENTIFIER"], "-f", readyfile]
            sc_process = execute_command_background(cmd)
            wait_start = time.time()
            while not os.path.exists(readyfile):
                if time.time() - wait_start > 30:
                    raise Exception(
                        "Sauce Connect Proxy is still not ready after 30 seconds, aborting!"
                    )
                time.sleep(1)
            print("Sauce Connect Proxy is ready, continuing...")

        if needs_clean:
            execute_bazel_clean(bazel_binary, platform)

        if not test_only:
            execute_bazel_build(
                bazel_binary,
                platform,
                config.get("build_flags", []),
                config.get("build_targets", None),
                None,
                incompatible_flags,
            )
            if save_but:
                upload_bazel_binary(platform)

        if not build_only:
            test_bep_file = os.path.join(tmpdir, "test_bep.json")
            try:
                execute_bazel_test(
                    bazel_binary,
                    platform,
                    config.get("test_flags", []),
                    config.get("test_targets", None),
                    test_bep_file,
                    monitor_flaky_tests,
                    incompatible_flags,
                )
                if has_flaky_tests(test_bep_file):
                    if monitor_flaky_tests:
                        # Upload the BEP logs from Bazel builds for later analysis on flaky tests
                        build_id = os.getenv("BUILDKITE_BUILD_ID")
                        pipeline_slug = os.getenv("BUILDKITE_PIPELINE_SLUG")
                        execute_command(
                            [
                                gsutil_command(),
                                "cp",
                                test_bep_file,
                                "gs://bazel-buildkite-stats/flaky-tests-bep/"
                                + pipeline_slug
                                + "/"
                                + build_id
                                + ".json",
                            ]
                        )
            finally:
                upload_test_logs(test_bep_file, tmpdir)
    finally:
        if sc_process:
            sc_process.terminate()
            try:
                sc_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                sc_process.kill()
        if tmpdir:
            shutil.rmtree(tmpdir)
