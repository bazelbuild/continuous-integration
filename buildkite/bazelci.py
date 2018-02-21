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
import base64
import codecs
import hashlib
import json
import multiprocessing
import os
import os.path
import random
import re
from shutil import copyfile
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.request
from github3 import login
from urllib.request import url2pathname
from urllib.parse import urlparse

# Initialize the random number generator.
random.seed()


class BuildkiteException(Exception):
    """
    Raised whenever something goes wrong and we should exit with an error.
    """
    pass


class BinaryUploadRaceException(Exception):
    """
    Raised when try_publish_binaries wasn't able to publish a set of binaries,
    because the generation of the current file didn't match the expected value.
    """
    pass


class BazelTestFailedException(Exception):
    """
    Raised when a Bazel test fails.
    """
    pass


class BazelTestFailedException(Exception):
    """
    Raised when a Bazel build fails.
    """
    pass


def eprint(*args, **kwargs):
    """
    Print to stderr and flush (just in case).
    """
    print(*args, flush=True, file=sys.stderr, **kwargs)


def downstream_projects():
    return {
        "Bazel Remote Execution": {
            "git_repository": "https://github.com/bazelbuild/bazel.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/bazel-remote-execution-postsubmit.json"
        },
        "BUILD_file_generator": {
            "git_repository": "https://github.com/bazelbuild/BUILD_file_generator.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/BUILD_file_generator-postsubmit.json"
        },
        "bazel-toolchains": {
            "git_repository": "https://github.com/bazelbuild/bazel-toolchains.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/bazel-toolchains-postsubmit.json"
        },
        "buildtools": {
            "git_repository": "https://github.com/bazelbuild/buildtools.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/buildtools-postsubmit.json"
        },
        "CLion Plugin": {
            "git_repository": "https://github.com/bazelbuild/intellij.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/clion-postsubmit.json"
        },
        "Eclipse Plugin": {
            "git_repository": "https://github.com/bazelbuild/eclipse.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/eclipse-postsubmit.json"
        },
        "Gerrit": {
            "git_repository": "https://gerrit.googlesource.com/gerrit.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/gerrit-postsubmit.json"
        },
        "Google Logging": {
            "git_repository": "https://github.com/google/glog.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/glog-postsubmit.json"
        },
        "IntelliJ Plugin": {
            "git_repository": "https://github.com/bazelbuild/intellij.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/intellij-postsubmit.json"
        },
        "migration-tooling": {
            "git_repository": "https://github.com/bazelbuild/migration-tooling.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/migration-tooling-postsubmit.json"
        },
        "protobuf": {
            "git_repository": "https://github.com/google/protobuf.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/protobuf-postsubmit.json"
        },
        "re2": {
            "git_repository": "https://github.com/google/re2.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/re2-postsubmit.json"
        },
        "rules_appengine": {
            "git_repository": "https://github.com/bazelbuild/rules_appengine.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_appengine-postsubmit.json"
        },
        "rules_closure": {
            "git_repository": "https://github.com/bazelbuild/rules_closure.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_closure-postsubmit.json"
        },
        "rules_d": {
            "git_repository": "https://github.com/bazelbuild/rules_d.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_d-postsubmit.json"
        },
        "rules_go": {
            "git_repository": "https://github.com/bazelbuild/rules_go.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_go-postsubmit.json"
        },
        "rules_groovy": {
            "git_repository": "https://github.com/bazelbuild/rules_groovy.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_groovy-postsubmit.json"
        },
        "rules_gwt": {
            "git_repository": "https://github.com/bazelbuild/rules_gwt.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_gwt-postsubmit.json"
        },
        "rules_jsonnet": {
            "git_repository": "https://github.com/bazelbuild/rules_jsonnet.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_jsonnet-postsubmit.json"
        },
        "rules_k8s": {
            "git_repository": "https://github.com/bazelbuild/rules_k8s.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_k8s-postsubmit.json"
        },
        "rules_nodejs": {
            "git_repository": "https://github.com/bazelbuild/rules_nodejs.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_nodejs-postsubmit.json"
        },
        "rules_perl": {
            "git_repository": "https://github.com/bazelbuild/rules_perl.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_perl-postsubmit.json"
        },
        "rules_python": {
            "git_repository": "https://github.com/bazelbuild/rules_python.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_python-postsubmit.json"
        },
        "rules_rust": {
            "git_repository": "https://github.com/bazelbuild/rules_rust.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_rust-postsubmit.json"
        },
        "rules_sass": {
            "git_repository": "https://github.com/bazelbuild/rules_sass.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_sass-postsubmit.json"
        },
        "rules_scala": {
            "git_repository": "https://github.com/bazelbuild/rules_scala.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_scala-postsubmit.json"
        },
        "rules_typescript": {
            "git_repository": "https://github.com/bazelbuild/rules_typescript.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_typescript-postsubmit.json"
        },
        # Enable once is resolved: https://github.com/bazelbuild/continuous-integration/issues/191
        # "rules_webtesting": {
        #     "git_repository": "https://github.com/bazelbuild/rules_webtesting.git",
        #     "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_webtesting-postsubmit.json"
        # },
        "skydoc": {
            "git_repository": "https://github.com/bazelbuild/skydoc.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/skydoc-postsubmit.json"
        },
        "subpar": {
            "git_repository": "https://github.com/google/subpar.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/subpar-postsubmit.json"
        },
        "TensorFlow": {
            "git_repository": "https://github.com/tensorflow/tensorflow.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/tensorflow-postsubmit.json"
        },
        "TensorFlow Serving": {
            "git_repository": "https://github.com/tensorflow/serving.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/tensorflow-serving-postsubmit.json"
        }
    }


def python_binary(platform=None):
    if platform == "windows":
        return "python.exe"
    return "python3.6"


def bazelcipy_url():
    """
    URL to the latest version of this script.
    """
    return "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py"


def platforms_info():
    """
    Returns a map containing all supported platform names as keys, with the
    values being the platform name in a human readable format, and a the
    buildkite-agent's working directory.
    """
    return {
        "ubuntu1404": {
            "name": "Ubuntu 14.04",
            "agent-directory": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}"
        },
        "ubuntu1604": {
            "name": "Ubuntu 16.04",
            "agent-directory": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}"
        },
        "macos": {
            "name": "macOS",
            "agent-directory": "/usr/local/var/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}"
        },
        "windows": {
            "name": "Windows",
            "agent-directory": "d:/build/${BUILDKITE_AGENT_NAME}",
        }
    }


def flaky_test_meme_url():
    urls = ["https://storage.googleapis.com/bazel-buildkite-memes/flaky_tests_1.jpg",
            "https://storage.googleapis.com/bazel-buildkite-memes/flaky_tests_2.jpg"]
    return random.choice(urls)


def downstream_projects_root(platform):
    downstream_projects_dir = os.path.expandvars(
        "${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects")
    path = os.path.join(agent_directory(platform), downstream_projects_dir)
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def agent_directory(platform):
    return os.path.expandvars(platforms_info()[platform]["agent-directory"])


def supported_platforms():
    return set(platforms_info().keys())


def fetch_configs(http_url):
    """
    If specified fetches the build configuration from http_url, else tries to
    read it from .bazelci/config.json.
    Returns the json configuration as a python data structure.
    """
    if http_url is None:
        with open(".bazelci/config.json", "r") as fd:
            return json.load(fd)
    with urllib.request.urlopen(http_url) as resp:
        reader = codecs.getreader("utf-8")
        return json.load(reader(resp))


def print_collapsed_group(name):
    eprint("\n--- {0}\n".format(name))


def print_expanded_group(name):
    eprint("\n+++ {0}\n".format(name))


def execute_commands(config, platform, git_repository, use_but, save_but,
                     build_only, test_only):
    fail_pipeline = False
    tmpdir = None
    bazel_binary = "bazel"
    commit = os.getenv("BUILDKITE_COMMIT")
    try:
        if git_repository:
            clone_git_repository(git_repository, platform)
        else:
            git_repository = os.getenv("BUILDKITE_REPO")
        cleanup()
        tmpdir = tempfile.mkdtemp()
        if use_but:
            print_collapsed_group("Downloading Bazel under test")
            bazel_binary = download_bazel_binary(tmpdir, platform)
        print_bazel_version_info(bazel_binary)
        execute_shell_commands(config.get("shell_commands", None))
        execute_bazel_run(bazel_binary, config.get("run_targets", None))
        if not test_only:
            build_bep_file = os.path.join(tmpdir, "build_bep.json")
            if is_pull_request():
                update_pull_request_build_status(git_repository, commit, "pending", None)
            try:
                execute_bazel_build(bazel_binary, platform, config.get("build_flags", []),
                                    config.get("build_targets", None), build_bep_file)
                if is_pull_request():
                    invocation_id = bes_invocation_id(build_bep_file)
                    update_pull_request_build_status(git_repository, commit, "success", invocation_id)
                if save_but:
                    upload_bazel_binary()
            except BazelBuildFailedException:
                if is_pull_request():
                    invocation_id = bes_invocation_id(build_bep_file)
                    update_pull_request_build_status(git_repository, commit, "failure", invocation_id)
                fail_pipeline = True
        if not fail_pipeline and not build_only:
            test_bep_file = os.path.join(tmpdir, "test_bep.json")
            try:
                if is_pull_request():
                    update_pull_request_test_status(git_repository, commit, "pending", None)
                execute_bazel_test(bazel_binary, platform, config.get("test_flags", []),
                                   config.get("test_targets", None), test_bep_file)
                if has_flaky_tests(test_bep_file):
                    show_image(flaky_test_meme_url(), "Flaky Tests")
                    # We also treat flaky tests as test failures
                    raise BazelTestFailedException
                if is_pull_request():
                    invocation_id = bes_invocation_id(test_bep_file)
                    update_pull_request_test_status(git_repository, commit, "success", invocation_id)
            except BazelTestFailedException:
                if is_pull_request():
                    invocation_id = bes_invocation_id(test_bep_file)
                    failed_tests = tests_with_status(test_bep_file, status="FAILED")
                    timed_out_tests = tests_with_status(test_bep_file, status="TIMEOUT")
                    flaky_tests = tests_with_status(test_bep_file, status="FLAKY")
                    update_pull_request_test_status(git_repository, commit, "success", invocation_id,
                                                    len(failed_tests), len(timed_out_tests), len(flaky_tests))
                fail_pipeline = True

            upload_test_logs(test_bep_file, tmpdir)
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir)
        cleanup()

    if fail_pipeline:
        raise BuildkiteException("At least one test failed or was flaky.")

def tests_with_status(bep_file, status):
    return set(label for label, _ in test_logs_for_status(bep_file, status=status))

def fetch_github_token():
    try:
        execute_command(
            ["gsutil", "cp", "gs://bazel-encrypted-secrets/github-token.enc", "github-token.enc"])
        return subprocess.check_output(["gcloud", "kms", "decrypt", "--location", "global", "--keyring", "buildkite",
                                        "--key", "github-token", "--ciphertext-file", "github-token.enc",
                                        "--plaintext-file", "-"]).decode("utf-8").strip()
    finally:
        os.remove("github-token.enc")


def owner_repository_from_url(git_repository):
    m = re.search(r"/([^/]+)/([^/]+)\.git$", git_repository)
    owner = m.group(1)
    repository = m.group(2)
    return (owner, repository)


def update_pull_request_status(git_repository, commit, state, invocation_id, description, context):
    gh = login(token=fetch_github_token())
    owner, repo = owner_repository_from_url(git_repository)
    repo = gh.repository(owner=owner, repository=repo)
    results_url = None
    if invocation_id:
        results_url = "https://source.cloud.google.com/results/invocations/" + invocation_id
    repo.create_status(sha=commit, state=state, target_url=results_url, description=description, context=context)


def update_pull_request_build_status(git_repository, commit, state, invocation_id):
    description = ""
    if state == "pending":
        description = "Running ..."
    elif state == "failure":
        description = "Failed"
    elif state == "success":
        description = "Succeeded"
    update_pull_request_status(git_repository, commit, state, invocation_id, description, "bazel build")


def update_pull_request_test_status(git_repository, commit, state, invocation_id, failed=0, timed_out=0,
                                    flaky=0):
    description = ""
    if state == "pending":
        description = "Running ..."
    elif state == "failure":
        description = "{0} tests failed, {1} tests timed out, {2} tests are flaky".format(failed, timed_out, flaky)
    elif state == "success":
        description = "All Tests Passed"
    update_pull_request_status(git_repository, commit, state, invocation_id, description, "bazel test")


def is_pull_request():
    third_party_repo = os.getenv("BUILDKITE_PULL_REQUEST_REPO", "")
    return len(third_party_repo) > 0


def bes_invocation_id(bep_file):
    targets = []
    raw_data = ""
    with open(bep_file) as f:
        raw_data = f.read()
    decoder = json.JSONDecoder()

    pos = 0
    while pos < len(raw_data):
        bep_obj, size = decoder.raw_decode(raw_data[pos:])
        if "started" in bep_obj:
            return bep_obj["started"]["uuid"]
        pos += size + 1
    return None


def show_image(url, alt):
    eprint("\033]1338;url='\"{0}\"';alt='\"{1}\"'\a\n".format(url, alt))


def has_flaky_tests(bep_file):
    return len(test_logs_for_status(bep_file, status="FLAKY")) > 0


def print_bazel_version_info(bazel_binary):
    print_collapsed_group("Bazel Info")
    execute_command([bazel_binary, "version"])
    execute_command([bazel_binary, "info"])


def upload_bazel_binary():
    print_collapsed_group("Uploading Bazel under test")
    execute_command(["buildkite-agent", "artifact", "upload", "bazel-bin/src/bazel"])


def download_bazel_binary(dest_dir, platform):
    source_step = create_label(platform, "Bazel", build_only=True)
    execute_command(["buildkite-agent", "artifact", "download",
                     "bazel-bin/src/bazel", dest_dir, "--step", source_step])
    bazel_binary_path = os.path.join(dest_dir, "bazel-bin/src/bazel")
    st = os.stat(bazel_binary_path)
    os.chmod(bazel_binary_path, st.st_mode | stat.S_IEXEC)
    return bazel_binary_path


def clone_git_repository(git_repository, platform):
    root = downstream_projects_root(platform)
    project_name = re.search(r"/([^/]+)\.git$", git_repository).group(1)
    clone_path = os.path.join(root, project_name)
    print_collapsed_group("Fetching " + project_name + " sources")
    if os.path.exists(clone_path):
        os.chdir(clone_path)
        execute_command(["git", "remote", "set-url", "origin", git_repository])
        execute_command(["git", "clean", "-fdqx"])
        execute_command(["git", "submodule", "foreach", "--recursive", "git", "clean", "-fdqx"])
        # sync to the latest commit of HEAD. Unlikely git pull this also works after
        # a force push.
        execute_command(["git", "fetch", "origin"])
        remote_head = subprocess.check_output(["git", "symbolic-ref", "refs/remotes/origin/HEAD"])
        remote_head = remote_head.decode("utf-8")
        remote_head = remote_head.rstrip()
        execute_command(["git", "reset", remote_head, "--hard"])
        execute_command(["git", "submodule", "sync", "--recursive"])
        execute_command(["git", "submodule", "update", "--init", "--recursive", "--force"])
        execute_command(["git", "submodule", "foreach", "--recursive", "git", "reset", "--hard"])
        execute_command(["git", "clean", "-fdqx"])
        execute_command(["git", "submodule", "foreach", "--recursive", "git", "clean", "-fdqx"])
    else:
        execute_command(["git", "clone", "--recurse-submodules", git_repository, clone_path])
        os.chdir(clone_path)


def cleanup():
    print_collapsed_group("Cleanup")
    if os.path.exists("WORKSPACE"):
        execute_command(["bazel", "clean", "--expunge"])


def execute_shell_commands(commands):
    if not commands:
        return
    print_collapsed_group("Setup (Shell Commands)")
    shell_command = "\n".join(commands)
    execute_command([shell_command], shell=True)


def execute_bazel_run(bazel_binary, targets):
    if not targets:
        return
    print_collapsed_group("Setup (Run Targets)")
    for target in targets:
        execute_command([bazel_binary, "run", "--curses=yes",
                         "--color=yes", "--verbose_failures", target])


def remote_caching_flags(platform):
    common_flags = ["--bes_backend=buildeventservice.googleapis.com", "--bes_best_effort=false",
                    "--bes_timeout=10s", "--tls_enabled", "--project_id=bazel-public",
                    "--remote_instance_name=projects/bazel-public",
                    "--experimental_remote_spawn_cache",
                    "--remote_timeout=10", "--remote_cache=remotebuildexecution.googleapis.com",
                    "--experimental_remote_platform_override=properties:{name:\"platform\" value:\"" + platform + "\"}"]
    if platform in ["ubuntu1404", "ubuntu1604"]:
        return common_flags + ["--google_default_credentials"]
    elif platform == "macos":
        return common_flags + ["--google_credentials=/Users/ci/GoogleDrive/bazel-public-e29b1f995cb1.json"]
    return []


def remote_enabled(flags):
    # Detect if the project configuration enabled its own remote caching / execution.
    remote_flags = ["--remote_executor", "--remote_cache", "--remote_http_cache"]
    for flag in flags:
        for remote_flag in remote_flags:
            if flag.startswith(remote_flag):
                return True
    return False


def execute_bazel_build(bazel_binary, platform, flags, targets, bep_file):
    if not targets:
        return
    print_expanded_group("Build")
    num_jobs = str(multiprocessing.cpu_count())
    common_flags = ["--show_progress_rate_limit=5", "--curses=yes", "--color=yes", "--keep_going",
                    "--jobs=" + num_jobs, "--build_event_json_file=" + bep_file,
                    "--experimental_build_event_json_file_path_conversion=false"]
    caching_flags = []
    if not remote_enabled(flags):
        caching_flags = remote_caching_flags(platform)
    try:
        execute_command([bazel_binary, "build"] + common_flags + caching_flags + flags + targets)
    except subprocess.CalledProcessError as e:
        raise BazelBuildFailedException("bazel build failed with exit code {}".format(e.returncode))


def execute_bazel_test(bazel_binary, platform, flags, targets, bep_file):
    if not targets:
        return
    print_expanded_group("Test")
    num_jobs = str(multiprocessing.cpu_count())
    common_flags = ["--show_progress_rate_limit=5", "--curses=yes", "--color=yes", "--keep_going",
                    "--flaky_test_attempts=3", "--build_tests_only",
                    "--jobs=" + num_jobs, "--local_test_jobs=" + num_jobs,
                    "--build_event_json_file=" + bep_file,
                    "--experimental_build_event_json_file_path_conversion=false"]
    caching_flags = []
    if not remote_enabled(flags):
        caching_flags = remote_caching_flags(platform)
    try:
        execute_command([bazel_binary, "test"] + common_flags + caching_flags + flags + targets)
    except subprocess.CalledProcessError as e:
        raise BazelTestFailedException("bazel test failed with exit code {}".format(e.returncode))


def upload_test_logs(bep_file, tmpdir):
    if not os.path.exists(bep_file):
        return
    test_logs = test_logs_to_upload(bep_file, tmpdir)
    if test_logs:
        cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            print_collapsed_group("Uploading test logs")
            execute_command(["buildkite-agent", "artifact", "upload", "*/**/*.log"])
        finally:
            os.chdir(cwd)


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
                eprint("new_path: " + new_path)
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                copyfile(test_log, new_path)
                new_paths.append(new_path)
                attempt += 1
            except IOError as err:
                # Log error and ignore.
                eprint(err)
    return new_paths


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


def test_logs_for_status(bep_file, status):
    targets = []
    raw_data = ""
    with open(bep_file) as f:
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


def execute_command(args, shell=False, fail_if_nonzero=True):
    eprint(" ".join(args))
    return subprocess.run(args, shell=shell, check=fail_if_nonzero).returncode


def untrusted_code_verification_step():
    return """
  - block: \"Untrusted Code Verification\"
    prompt: \"Did you review this pull request for malicious code?\""""

def print_project_pipeline(platform_configs, project_name, http_config,
                           git_repository, use_but):
    pipeline_steps = []
    if is_pull_request():
        pipeline_steps.append(untrusted_code_verification_step())
    for platform, _ in platform_configs.items():
        step = runner_step(platform, project_name, http_config, git_repository, use_but)
        pipeline_steps.append(step)

    print_pipeline(pipeline_steps)


def runner_step(platform, project_name=None, http_config=None,
                git_repository=None, use_but=False):
    command = python_binary(platform) + " bazelci.py runner --platform=" + platform
    if http_config:
        command += " --http_config=" + http_config
    if git_repository:
        command += " --git_repository=" + git_repository
    if use_but:
        command += " --use_but"
    label = create_label(platform, project_name)
    return """
  - label: \"{0}\"
    command: \"{1}\\n{2}\"
    agents:
      - \"os={3}\"""".format(label, fetch_bazelcipy_command(), command, platform)


def print_pipeline(steps):
    print("steps:")
    for step in steps:
        print(step)


def wait_step():
    return """
  - wait"""


def http_config_flag(http_config):
    if http_config is not None:
        return "--http_config=" + http_config
    return ""


def fetch_bazelcipy_command():
    return "curl -s {0} -o bazelci.py".format(bazelcipy_url())


def upload_project_pipeline_step(project_name, git_repository, http_config):
    pipeline_command = ("{0} bazelci.py project_pipeline --project_name=\\\"{1}\\\" " +
                        "--use_but --git_repository={2}").format(python_binary(), project_name,
                                                                 git_repository)
    if http_config:
        pipeline_command += " --http_config=" + http_config
    pipeline_command += " | buildkite-agent pipeline upload"

    return """
  - label: \"Setup {0}\"
    command: \"{1}\\n{2}\"
    agents:
      - \"pipeline=true\"""".format(project_name, fetch_bazelcipy_command(),
                                    pipeline_command)


def create_label(platform, project_name, build_only=False, test_only=False):
    if build_only and test_only:
        raise BuildkiteException("build_only and test_only cannot be true at the same time")
    platform_name = platforms_info()[platform]["name"]

    if build_only:
        label = "Build "
    elif test_only:
        label = "Test "
    else:
        label = ""

    if project_name:
        label += "{0} ({1})".format(project_name, platform_name)
    else:
        label += platform_name

    return label


def bazel_build_step(platform, project_name, http_config=None, build_only=False, test_only=False):
    pipeline_command = python_binary(platform) + " bazelci.py runner"
    if build_only:
        pipeline_command += " --build_only --save_but"
    if test_only:
        pipeline_command += " --test_only"
    if http_config:
        pipeline_command += " --http_config=" + http_config
    label = create_label(platform, project_name, build_only, test_only)
    pipeline_command += " --platform=" + platform

    return """
  - label: \"{0}\"
    command: \"{1}\\n{2}\"
    agents:
      - \"os={3}\"""".format(label, fetch_bazelcipy_command(),
                             pipeline_command, platform)


def publish_bazel_binaries_step():
    command = python_binary() + " bazelci.py publish_binaries"
    return """
  - label: \"Publish Bazel Binaries\"
    command: \"{0}\\n{1}\"
    agents:
      - \"pipeline=true\"""".format(fetch_bazelcipy_command(), command)


def print_bazel_postsubmit_pipeline(configs, http_config):
    if not configs:
        raise BuildkiteException("Bazel postsubmit pipeline configuration is empty.")
    if set(configs.keys()) != set(supported_platforms()):
        raise BuildkiteException("Bazel postsubmit pipeline needs to build Bazel on all supported platforms.")

    pipeline_steps = []
    for platform, config in configs.items():
        pipeline_steps.append(bazel_build_step(platform, "Bazel", http_config, build_only=True))
    pipeline_steps.append(wait_step())

    # todo move this to the end with a wait step.
    pipeline_steps.append(publish_bazel_binaries_step())

    for platform, config in configs.items():
        pipeline_steps.append(bazel_build_step(platform, "Bazel", http_config, test_only=True))

    for project, config in downstream_projects().items():
        git_repository = config["git_repository"]
        http_config = config.get("http_config", None)
        pipeline_steps.append(upload_project_pipeline_step(project,
                                                           git_repository, http_config))

    print_pipeline(pipeline_steps)


def bazelci_builds_download_url(platform, build_number):
    return "https://storage.googleapis.com/bazel-builds/artifacts/{0}/{1}/bazel".format(platform, build_number)


def bazelci_builds_upload_url(platform, build_number):
    return "gs://bazel-builds/artifacts/{0}/{1}/bazel".format(platform, build_number)


def bazelci_builds_metadata_url():
    return "gs://bazel-builds/metadata/latest_fully_tested.json"


def latest_generation_and_build_number():
    output = None
    attempt = 0
    while attempt < 5:
        output = subprocess.check_output(
            ["gsutil", "stat", bazelci_builds_metadata_url()])
        match = re.search("Generation:[ ]*([0-9]+)", output.decode("utf-8"))
        if not match:
            raise BuildkiteException("Couldn't parse generation. gsutil output format changed?")
        generation = match.group(1)

        match = re.search(r"Hash \(md5\):[ ]*([^\s]+)", output.decode("utf-8"))
        if not match:
            raise BuildkiteException("Couldn't parse md5 hash. gsutil output format changed?")
        expected_md5hash = base64.b64decode(match.group(1))

        output = subprocess.check_output(
            ["gsutil", "cat", bazelci_builds_metadata_url()])
        hasher = hashlib.md5()
        hasher.update(output)
        actual_md5hash = hasher.digest()

        if expected_md5hash == actual_md5hash:
            break
        attempt += 1
    info = json.loads(output.decode("utf-8"))
    return (generation, info["build_number"])


def sha256_hexdigest(filename):
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(65536), b''):
            sha256.update(block)
    return sha256.hexdigest()


def try_publish_binaries(build_number, expected_generation):
    tmpdir = tempfile.mkdtemp()
    try:
        info = {
            "build_number": build_number,
            "git_commit": os.environ["BUILDKITE_COMMIT"],
            "platforms": {}
        }
        for platform in supported_platforms():
            bazel_binary_path = download_bazel_binary(tmpdir, platform)
            execute_command(["gsutil", "cp", "-a", "public-read", bazel_binary_path,
                             bazelci_builds_upload_url(platform, build_number)])
            info["platforms"][platform] = {
                "url": bazelci_builds_download_url(platform, build_number),
                "sha256": sha256_hexdigest(bazel_binary_path),
            }

        info_file = os.path.join(tmpdir, "info.json")
        with open(info_file, mode="w", encoding="utf-8") as fp:
            json.dump(info, fp)

        try:
            execute_command([
                "gsutil",
                "-h", "x-goog-if-generation-match:" + expected_generation,
                "-h", "Content-Type:application/json",
                "cp", "-a", "public-read",
                info_file, bazelci_builds_metadata_url()])
        except subprocess.CalledProcessError:
            raise BinaryUploadRaceException()
    finally:
        shutil.rmtree(tmpdir)


def publish_binaries():
    """
    Publish Bazel binaries to GCS.
    """
    current_build_number = os.environ.get("BUILDKITE_BUILD_NUMBER", None)
    if not current_build_number:
        raise BuildkiteException("Not running inside Buildkite")
    current_build_number = int(current_build_number)

    for _ in range(5):
        latest_generation, latest_build_number = latest_generation_and_build_number()

        if current_build_number <= latest_build_number:
            eprint(("Current build '{0}' is not newer than latest published '{1}'. " +
                    "Skipping publishing of binaries.").format(current_build_number,
                                                               latest_build_number))
            break

        try:
            try_publish_binaries(current_build_number, latest_generation)
        except BinaryUploadRaceException:
            # Retry.
            continue

        eprint("Successfully updated '{0}' to binaries from build {1}."
               .format(bazelci_builds_metadata_url(), current_build_number))
        break
    else:
        raise BuildkiteException("Could not publish binaries, ran out of attempts.")


def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(description='Bazel Continuous Integration Script')

    subparsers = parser.add_subparsers(dest="subparsers_name")

    bazel_postsubmit_pipeline = subparsers.add_parser("bazel_postsubmit_pipeline")
    bazel_postsubmit_pipeline.add_argument("--http_config", type=str)
    bazel_postsubmit_pipeline.add_argument("--git_repository", type=str)

    project_pipeline = subparsers.add_parser("project_pipeline")
    project_pipeline.add_argument("--project_name", type=str)
    project_pipeline.add_argument("--http_config", type=str)
    project_pipeline.add_argument("--git_repository", type=str)
    project_pipeline.add_argument("--use_but", type=bool, nargs="?", const=True)

    runner = subparsers.add_parser("runner")
    runner.add_argument("--platform", action="store", choices=list(supported_platforms()))
    runner.add_argument("--http_config", type=str)
    runner.add_argument("--git_repository", type=str)
    runner.add_argument("--use_but", type=bool, nargs="?", const=True)
    runner.add_argument("--save_but", type=bool, nargs="?", const=True)
    runner.add_argument("--build_only", type=bool, nargs="?", const=True)
    runner.add_argument("--test_only", type=bool, nargs="?", const=True)

    runner = subparsers.add_parser("publish_binaries")

    args = parser.parse_args()

    try:
        if args.subparsers_name == "bazel_postsubmit_pipeline":
            configs = fetch_configs(args.http_config)
            print_bazel_postsubmit_pipeline(configs.get("platforms", None), args.http_config)
        elif args.subparsers_name == "project_pipeline":
            configs = fetch_configs(args.http_config)
            print_project_pipeline(configs.get("platforms", None), args.project_name,
                                   args.http_config, args.git_repository, args.use_but)
        elif args.subparsers_name == "runner":
            configs = fetch_configs(args.http_config)
            execute_commands(configs.get("platforms", None)[args.platform],
                             args.platform, args.git_repository, args.use_but, args.save_but,
                             args.build_only, args.test_only)
        elif args.subparsers_name == "publish_binaries":
            publish_binaries()
        else:
            parser.print_help()
            return 2
    except BuildkiteException as e:
        eprint(str(e))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
