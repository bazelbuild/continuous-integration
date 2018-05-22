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
import datetime
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
import yaml
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


class BazelBuildFailedException(Exception):
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
        # Removed until issues in https://github.com/bazelbuild/bazel/issues/4979 is fully resolved
        # "Android Testing": {
        #    "git_repository": "https://github.com/googlesamples/android-testing.git",
        #    "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/android-testing-postsubmit.yml"
        # },
        "Bazel Remote Execution": {
            "git_repository": "https://github.com/bazelbuild/bazel.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/bazel-remote-execution-postsubmit.yml"
        },
        "BUILD_file_generator": {
            "git_repository": "https://github.com/bazelbuild/BUILD_file_generator.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/BUILD_file_generator/master/.bazelci/presubmit.yml"
        },
        "bazel-toolchains": {
            "git_repository": "https://github.com/bazelbuild/bazel-toolchains.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/bazel-toolchains/master/.bazelci/presubmit.yml"
        },
        "bazel-skylib": {
            "git_repository": "https://github.com/bazelbuild/bazel-skylib.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/bazel-skylib/master/.bazelci/presubmit.yml"
        },
        "buildtools": {
            "git_repository": "https://github.com/bazelbuild/buildtools.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/buildtools/master/.bazelci/presubmit.yml"
        },
        "CLion Plugin": {
            "git_repository": "https://github.com/bazelbuild/intellij.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/clion-postsubmit.yml"
        },
        "Eclipse Plugin": {
            "git_repository": "https://github.com/bazelbuild/eclipse.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/eclipse/master/.bazelci/presubmit.yml"
        },
        "Gerrit": {
            "git_repository": "https://gerrit.googlesource.com/gerrit.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/gerrit-postsubmit.yml"
        },
        "Google Logging": {
            "git_repository": "https://github.com/google/glog.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/glog-postsubmit.yml"
        },
        "IntelliJ Plugin": {
            "git_repository": "https://github.com/bazelbuild/intellij.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/intellij-postsubmit.yml"
        },
        "migration-tooling": {
            "git_repository": "https://github.com/bazelbuild/migration-tooling.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/migration-tooling/master/.bazelci/presubmit.yml"
        },
        "protobuf": {
            "git_repository": "https://github.com/google/protobuf.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/protobuf-postsubmit.yml"
        },
        "re2": {
            "git_repository": "https://github.com/google/re2.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/re2-postsubmit.yml"
        },
        "rules_appengine": {
            "git_repository": "https://github.com/bazelbuild/rules_appengine.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_appengine/master/.bazelci/presubmit.yml"
        },
        "rules_apple": {
            "git_repository": "https://github.com/bazelbuild/rules_apple.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_apple/master/.bazelci/presubmit.yml"
        },
        "rules_closure": {
            "git_repository": "https://github.com/bazelbuild/rules_closure.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_closure/master/.bazelci/presubmit.yml"
        },
        "rules_d": {
            "git_repository": "https://github.com/bazelbuild/rules_d.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_d/master/.bazelci/presubmit.yml"
        },
        "rules_docker": {
            "git_repository": "https://github.com/bazelbuild/rules_docker.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_docker/master/.bazelci/presubmit.yml"
        },
        "rules_go": {
            "git_repository": "https://github.com/bazelbuild/rules_go.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_go/master/.bazelci/presubmit.yml"
        },
        "rules_groovy": {
            "git_repository": "https://github.com/bazelbuild/rules_groovy.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_groovy/master/.bazelci/presubmit.yml"
        },
        "rules_gwt": {
            "git_repository": "https://github.com/bazelbuild/rules_gwt.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_gwt/master/.bazelci/presubmit.yml"
        },
        "rules_jsonnet": {
            "git_repository": "https://github.com/bazelbuild/rules_jsonnet.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_jsonnet/master/.bazelci/presubmit.yml"
        },
        "rules_kotlin": {
            "git_repository": "https://github.com/bazelbuild/rules_kotlin.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_kotlin/master/.bazelci/presubmit.yml"
        },
        "rules_k8s": {
            "git_repository": "https://github.com/bazelbuild/rules_k8s.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_k8s/master/.bazelci/presubmit.yml"
        },
        "rules_nodejs": {
            "git_repository": "https://github.com/bazelbuild/rules_nodejs.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_nodejs/master/.bazelci/presubmit.yml"
        },
        "rules_perl": {
            "git_repository": "https://github.com/bazelbuild/rules_perl.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_perl/master/.bazelci/presubmit.yml"
        },
        "rules_python": {
            "git_repository": "https://github.com/bazelbuild/rules_python.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_python/master/.bazelci/presubmit.yml"
        },
        "rules_rust": {
            "git_repository": "https://github.com/bazelbuild/rules_rust.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_rust/master/.bazelci/presubmit.yml"
        },
        "rules_sass": {
            "git_repository": "https://github.com/bazelbuild/rules_sass.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_sass/master/.bazelci/presubmit.yml"
        },
        "rules_scala": {
            "git_repository": "https://github.com/bazelbuild/rules_scala.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_scala/master/.bazelci/presubmit.yml"
        },
        "rules_typescript": {
            "git_repository": "https://github.com/bazelbuild/rules_typescript.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_typescript/master/.bazelci/presubmit.yml"
        },
        # Enable once is resolved: https://github.com/bazelbuild/continuous-integration/issues/191
        # "rules_webtesting": {
        #     "git_repository": "https://github.com/bazelbuild/rules_webtesting.git",
        #     "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_webtesting-postsubmit.yml"
        # },
        "skydoc": {
            "git_repository": "https://github.com/bazelbuild/skydoc.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/skydoc/master/.bazelci/presubmit.yml"
        },
        "subpar": {
            "git_repository": "https://github.com/google/subpar.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/subpar-postsubmit.yml"
        },
        "TensorFlow": {
            "git_repository": "https://github.com/tensorflow/tensorflow.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/tensorflow-postsubmit.yml"
        },
        "TensorFlow Serving": {
            "git_repository": "https://github.com/tensorflow/serving.git",
            "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/tensorflow-serving-postsubmit.yml"
        }
    }


def python_binary(platform=None):
    if platform == "windows":
        return "python.exe"
    return "python3.6"


def is_windows():
    return os.name == "nt"


def gsutil_command():
    if is_windows():
        return "gsutil.cmd"
    return "gsutil"


def gcloud_command():
    if is_windows():
        return "gcloud.cmd"
    return "gcloud"


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
            "emoji-name": ":ubuntu: 14.04",
            "agent-directory": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}"
        },
        "ubuntu1604": {
            "name": "Ubuntu 16.04",
            "emoji-name": ":ubuntu: 16.04",
            "agent-directory": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}"
        },
        "macos": {
            "name": "macOS",
            "emoji-name": ":darwin:",
            "agent-directory": "/Users/buildkite/builds/${BUILDKITE_AGENT_NAME}"
        },
        "windows": {
            "name": "Windows",
            "emoji-name": ":windows:",
            "agent-directory": "c:/build/${BUILDKITE_AGENT_NAME}",
        }
    }


def flaky_test_meme_url():
    urls = ["https://storage.googleapis.com/bazel-buildkite-memes/flaky_tests_1.jpg",
            "https://storage.googleapis.com/bazel-buildkite-memes/flaky_tests_2.jpg",
            "https://storage.googleapis.com/bazel-buildkite-memes/flaky_tests_3.jpg"]
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


def fetch_configs(http_url, file_config):
    """
    If specified fetches the build configuration from file_config or http_url, else tries to
    read it from .bazelci/presubmit.yml.
    Returns the json configuration as a python data structure.
    """
    if file_config is not None and http_url is not None:
        raise BuildkiteException("file_config and http_url cannot be set at the same time")

    if file_config is not None:
        with open(file_config, "r") as fd:
            return yaml.load(fd)
    if http_url is not None:
        with urllib.request.urlopen(http_url) as resp:
            reader = codecs.getreader("utf-8")
            return yaml.load(reader(resp))
    with open(".bazelci/presubmit.yml", "r") as fd:
        return yaml.load(fd)


def print_collapsed_group(name):
    eprint("\n\n--- {0}\n\n".format(name))


def print_expanded_group(name):
    eprint("\n\n+++ {0}\n\n".format(name))


def execute_commands(config, platform, git_repository, use_but, save_but,
                     build_only, test_only):
    fail_pipeline = False
    tmpdir = None
    bazel_binary = "bazel"
    commit = os.getenv("BUILDKITE_COMMIT")
    build_only = build_only or "test_targets" not in config
    test_only = test_only or "build_targets" not in config
    if build_only and test_only:
        raise BuildkiteException("build_only and test_only cannot be true at the same time")
    try:
        if git_repository:
            clone_git_repository(git_repository, platform)
        else:
            git_repository = os.getenv("BUILDKITE_REPO")
        if is_pull_request() and not is_trusted_author(github_user_for_pull_request(), git_repository):
            update_pull_request_verification_status(git_repository, commit, state="success")
        tmpdir = tempfile.mkdtemp()
        if use_but:
            print_collapsed_group(":gcloud: Downloading Bazel Under Test")
            bazel_binary = download_bazel_binary(tmpdir, platform)
        print_bazel_version_info(bazel_binary)
        if platform == "windows":
            execute_batch_commands(config.get("batch_commands", None))
        else:
            execute_shell_commands(config.get("shell_commands", None))
        execute_bazel_run(bazel_binary, config.get("run_targets", None))
        if not test_only:
            build_bep_file = os.path.join(tmpdir, "build_bep.json")
            if is_pull_request():
                update_pull_request_build_status(
                    platform, git_repository, commit, "pending", None)
            try:
                execute_bazel_build(bazel_binary, platform, config.get("build_flags", []),
                                    config.get("build_targets", None), build_bep_file)
                if is_pull_request():
                    invocation_id = bes_invocation_id(build_bep_file)
                    update_pull_request_build_status(
                        platform, git_repository, commit, "success", invocation_id)
                if save_but:
                    upload_bazel_binary(platform)
            except BazelBuildFailedException:
                if is_pull_request():
                    invocation_id = bes_invocation_id(build_bep_file)
                    update_pull_request_build_status(
                        platform, git_repository, commit, "failure", invocation_id)
                fail_pipeline = True
        if (not fail_pipeline) and (not build_only):
            test_bep_file = os.path.join(tmpdir, "test_bep.json")
            try:
                if is_pull_request():
                    update_pull_request_test_status(
                        platform, git_repository, commit, "pending", None)
                execute_bazel_test(bazel_binary, platform, config.get("test_flags", []),
                                   config.get("test_targets", None), test_bep_file)
                if has_flaky_tests(test_bep_file):
                    show_image(flaky_test_meme_url(), "Flaky Tests")
                    if os.getenv("BUILDKITE_PIPELINE_SLUG") in ["bazel-bazel", "google-bazel-presubmit"]:
                        # Upload the BEP logs from Bazel builds for later analysis on flaky tests
                        build_id = os.getenv("BUILDKITE_BUILD_ID")
                        execute_command([gsutil_command(), "cp", test_bep_file, "gs://bazel-buildkite-stats/build_event_protocols/" + build_id + ".json"])
                if is_pull_request():
                    invocation_id = bes_invocation_id(test_bep_file)
                    update_pull_request_test_status(
                        platform, git_repository, commit, "success", invocation_id)
            except BazelTestFailedException:
                if is_pull_request():
                    invocation_id = bes_invocation_id(test_bep_file)
                    failed_tests = tests_with_status(
                        test_bep_file, status="FAILED")
                    timed_out_tests = tests_with_status(
                        test_bep_file, status="TIMEOUT")
                    flaky_tests = tests_with_status(
                        test_bep_file, status="FLAKY")

                    update_pull_request_test_status(platform, git_repository, commit, "failure", invocation_id,
                                                    len(failed_tests), len(timed_out_tests), len(flaky_tests))
                fail_pipeline = True

            upload_test_logs(test_bep_file, tmpdir)
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir)

    if fail_pipeline:
        raise BuildkiteException("At least one test failed or was flaky.")


def tests_with_status(bep_file, status):
    return set(label for label, _ in test_logs_for_status(bep_file, status=status))


__github_token__ = None


def fetch_github_token():
    global __github_token__
    if __github_token__:
        return __github_token__
    try:
        execute_command(
            [gsutil_command(), "cp", "gs://bazel-encrypted-secrets/github-token.enc", "github-token.enc"])
        __github_token__ = subprocess.check_output([gcloud_command(), "kms", "decrypt", "--location", "global", "--keyring", "buildkite",
                                                    "--key", "github-token", "--ciphertext-file", "github-token.enc",
                                                    "--plaintext-file", "-"]).decode("utf-8").strip()
        return __github_token__
    finally:
        os.remove("github-token.enc")


def owner_repository_from_url(git_repository):
    m = re.search(r"/([^/]+)/([^/]+)\.git$", git_repository)
    owner = m.group(1)
    repository = m.group(2)
    return (owner, repository)


def results_view_url(invocation_id, platform):
    if platform == "windows":
        return "https://github.com/bazelbuild/bazel/issues/4735"
    results_url = None
    if invocation_id:
        results_url = "https://source.cloud.google.com/results/invocations/" + invocation_id
    return results_url


def update_pull_request_status(git_repository, commit, state, details_url, description, context):
    gh = login(token=fetch_github_token())
    owner, repo = owner_repository_from_url(git_repository)
    repo = gh.repository(owner=owner, repository=repo)
    repo.create_status(sha=commit, state=state, target_url=details_url, description=description,
                       context=context)


def update_pull_request_verification_status(git_repository, commit, state):
    description = ""
    if state == "pending":
        description = "Waiting for a project member to verify this pull request."
    elif state == "success":
        description = "Verified"
    build_url = os.getenv("BUILDKITE_BUILD_URL")
    update_pull_request_status(git_repository, commit, state, build_url, description,
                               "Verify Pull Request")


def update_pull_request_build_status(platform, git_repository, commit, state, invocation_id):
    description = ""
    if state == "pending":
        description = "Building ..."
    elif state == "failure":
        description = "Failure"
    elif state == "success":
        description = "Success"
    update_pull_request_status(git_repository, commit, state, results_view_url(invocation_id, platform),
                               description, "bazel build ({0})".format(platforms_info()[platform]["name"]))


def update_pull_request_test_status(platform, git_repository, commit, state, invocation_id, num_failed=0,
                                    num_timed_out=0, num_flaky=0):
    description = ""
    if state == "pending":
        description = "Testing ..."
    elif state == "failure":
        if num_failed == 1:
            description = description + "{0} test failed, ".format(num_failed)
        elif num_failed > 0:
            description = description + "{0} tests failed, ".format(num_failed)

        if num_timed_out == 1:
            description = description + "{0} test timed out, ".format(num_timed_out)
        elif num_timed_out > 0:
            description = description + "{0} tests timed out, ".format(num_timed_out)

        if num_flaky == 1:
            description = description + "{0} test is flaky, ".format(num_flaky)
        elif num_flaky > 0:
            description = description + "{0} tests are flaky, ".format(num_flaky)

        if len(description) > 0:
            description = description[:-2]
        else:
            description = "Some tests didn't pass"
    elif state == "success":
        description = "All tests passed"
    update_pull_request_status(git_repository, commit, state, results_view_url(invocation_id, platform),
                               description, "bazel test ({0})".format(platforms_info()[platform]["name"]))


def is_pull_request():
    third_party_repo = os.getenv("BUILDKITE_PULL_REQUEST_REPO", "")
    return len(third_party_repo) > 0


def bes_invocation_id(bep_file):
    targets = []
    raw_data = ""
    with open(bep_file, encoding="utf-8") as f:
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
    print_collapsed_group(":information_source: Bazel Info")
    execute_command([bazel_binary, "--nomaster_bazelrc", "--bazelrc=/dev/null", "version"])
    execute_command([bazel_binary, "--nomaster_bazelrc", "--bazelrc=/dev/null", "info"])


def upload_bazel_binary(platform):
    print_collapsed_group(":gcloud: Uploading Bazel Under Test")
    binary_path = "bazel-bin/src/bazel"
    if platform == "windows":
        binary_path = r"bazel-bin\src\bazel"

    execute_command(["buildkite-agent", "artifact", "upload", binary_path])


def download_bazel_binary(dest_dir, platform):
    binary_path = "bazel-bin/src/bazel"
    if platform == "windows":
        binary_path = r"bazel-bin\src\bazel"

    source_step = create_label(platform, "Bazel", build_only=True)
    execute_command(["buildkite-agent", "artifact", "download",
                     binary_path, dest_dir, "--step", source_step])
    bazel_binary_path = os.path.join(dest_dir, binary_path)
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
        execute_command(["git", "submodule", "foreach",
                         "--recursive", "git", "clean", "-fdqx"])
        # sync to the latest commit of HEAD. Unlikely git pull this also works after
        # a force push.
        execute_command(["git", "fetch", "origin"])
        remote_head = subprocess.check_output(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"])
        remote_head = remote_head.decode("utf-8")
        remote_head = remote_head.rstrip()
        execute_command(["git", "reset", remote_head, "--hard"])
        execute_command(["git", "submodule", "sync", "--recursive"])
        execute_command(["git", "submodule", "update",
                         "--init", "--recursive", "--force"])
        execute_command(["git", "submodule", "foreach",
                         "--recursive", "git", "reset", "--hard"])
        execute_command(["git", "clean", "-fdqx"])
        execute_command(["git", "submodule", "foreach",
                         "--recursive", "git", "clean", "-fdqx"])
    else:
        if platform in ["ubuntu1404", "ubuntu1604"]:
            execute_command(
                ["git", "clone", "--recurse-submodules", "--reference",
                 "/var/lib/bazelbuild", git_repository, clone_path])
        elif platform in ["macos"]:
            execute_command(
                ["git", "clone", "--recurse-submodules", "--reference",
                 "/usr/local/var/bazelbuild", git_repository, clone_path])
        elif platform in ["windows"]:
            execute_command(
                ["git", "clone", "--recurse-submodules", "--reference",
                 "c:\\buildkite\\bazelbuild", git_repository, clone_path])
        else:
            execute_command(
                ["git", "clone", "--recurse-submodules", git_repository,
                 clone_path])
        os.chdir(clone_path)


def execute_batch_commands(commands):
    if not commands:
        return
    print_collapsed_group(":batch: Setup (Batch Commands)")
    batch_commands = "&".join(commands)
    return subprocess.run(batch_commands, shell=True, check=True).returncode

def execute_shell_commands(commands):
    if not commands:
        return
    print_collapsed_group(":bash: Setup (Shell Commands)")
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
    if is_pull_request():
        common_flags = ["--bes_backend=buildeventservice.googleapis.com",
                        "--bes_best_effort=false",
                        "--bes_timeout=10s",
                        "--tls_enabled",
                        "--project_id=bazel-public",
                        "--remote_instance_name=projects/bazel-public",
                        "--experimental_remote_spawn_cache",
                        "--remote_timeout=10",
                        "--remote_cache=remotebuildexecution.googleapis.com",
                        "--experimental_remote_platform_override=properties:{name:\"platform\" value:\"" + platform + "\"}"]
    else:
        common_flags = ["--remote_timeout=10",
                        "--experimental_remote_spawn_cache",
                        "--experimental_remote_platform_override=properties:{name:\"platform\" value:\"" + platform + "\"}",
                        "--remote_http_cache=https://storage.googleapis.com/bazel-buildkite-cache"]
    if platform in ["ubuntu1404", "ubuntu1604", "macos"]:
        return common_flags + ["--google_default_credentials"]
    return []


def remote_enabled(flags):
    # Detect if the project configuration enabled its own remote caching / execution.
    remote_flags = ["--remote_executor",
                    "--remote_cache", "--remote_http_cache"]
    for flag in flags:
        for remote_flag in remote_flags:
            if flag.startswith(remote_flag):
                return True
    return False


def concurrent_jobs():
    return str(multiprocessing.cpu_count())


def concurrent_test_jobs(platform):
    if platform == "windows":
        return str(multiprocessing.cpu_count() // 4)
    elif platform == "macos":
        return str(multiprocessing.cpu_count() // 2)
    else:
        return str(multiprocessing.cpu_count())


def common_flags(bep_file):
    return ["--show_progress_rate_limit=5",
            "--curses=yes",
            "--color=yes",
            "--keep_going",
            "--jobs=" + concurrent_jobs(),
            "--build_event_json_file=" + bep_file,
            "--experimental_build_event_json_file_path_conversion=false",
            "--announce_rc",
            "--sandbox_tmpfs_path=/tmp",
            "--experimental_multi_threaded_digest"]

def execute_bazel_build(bazel_binary, platform, flags, targets, bep_file):
    print_expanded_group(":bazel: Build")
    caching_flags = []
    if not remote_enabled(flags):
        caching_flags = remote_caching_flags(platform)
    try:
        execute_command([bazel_binary, "build"] + common_flags(bep_file) +
                         caching_flags + flags + targets)
    except subprocess.CalledProcessError as e:
        raise BazelBuildFailedException(
            "bazel build failed with exit code {}".format(e.returncode))


def execute_bazel_test(bazel_binary, platform, flags, targets, bep_file):
    print_expanded_group(":bazel: Test")
    test_flags = ["--flaky_test_attempts=3",
                  "--build_tests_only",
                  "--local_test_jobs=" + concurrent_test_jobs(platform)]
    caching_flags = []
    if not remote_enabled(flags):
        caching_flags = remote_caching_flags(platform)
    try:
        execute_command([bazel_binary, "test"] + common_flags(bep_file) +
                         test_flags + caching_flags + flags + targets)
    except subprocess.CalledProcessError as e:
        raise BazelTestFailedException(
            "bazel test failed with exit code {}".format(e.returncode))


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
                    test_logs.append(url2pathname(
                        urlparse(output["uri"]).path))
                targets.append((test_target, test_logs))
        pos += size + 1
    return targets


def execute_command(args, shell=False, fail_if_nonzero=True):
    eprint(" ".join(args))
    return subprocess.run(args, shell=shell, check=fail_if_nonzero).returncode


def untrusted_code_verification_step():
    return """
  - block: \"Verify Pull Request\"
    prompt: \"Did you review this pull request for malicious code?\""""


def is_trusted_author(github_user, git_repository):
    if not github_user or not git_repository:
        raise BuildkiteException("github_user and git_repository must be set.")

    gh = login(token=fetch_github_token())
    owner, repo = owner_repository_from_url(git_repository)
    repo = gh.repository(owner=owner, repository=repo)
    return repo.is_collaborator(github_user)


def github_user_for_pull_request():
    branch = os.getenv("BUILDKITE_BRANCH")
    user = branch.split(":", 1)
    return user[0]


def print_project_pipeline(platform_configs, project_name, http_config, file_config,
                           git_repository, use_but):
    pipeline_steps = []
    if is_pull_request():
        commit_author = github_user_for_pull_request()
        trusted_git_repository = git_repository or os.getenv("BUILDKITE_REPO")
        if is_pull_request() and not is_trusted_author(commit_author, trusted_git_repository):
            commit = os.getenv("BUILDKITE_COMMIT")
            update_pull_request_verification_status(trusted_git_repository, commit, state="pending")
            pipeline_steps.append(untrusted_code_verification_step())

    for platform, _ in platform_configs.items():
        step = runner_step(platform, project_name,
                           http_config, file_config, git_repository, use_but)
        pipeline_steps.append(step)

    print_pipeline(pipeline_steps)


def runner_step(platform, project_name=None, http_config=None,
                file_config=None, git_repository=None, use_but=False):
    command = python_binary(platform) + \
        " bazelci.py runner --platform=" + platform
    if http_config:
        command += " --http_config=" + http_config
    if file_config:
        command += " --file_config=" + file_config
    if git_repository:
        command += " --git_repository=" + git_repository
    if use_but:
        command += " --use_but"
    label = create_label(platform, project_name)
    return """
  - label: \"{0}\"
    command: \"{1}\\n{2}\"
    agents:
      kind: worker
      java: 8
      os: {3}""".format(label, fetch_bazelcipy_command(), command, platform)


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


def upload_project_pipeline_step(project_name, git_repository, http_config, file_config):
    pipeline_command = ("{0} bazelci.py project_pipeline --project_name=\\\"{1}\\\" " +
                        "--use_but --git_repository={2}").format(python_binary(), project_name,
                                                                 git_repository)
    if http_config:
        pipeline_command += " --http_config=" + http_config
    if file_config:
        pipeline_command += " --file_config=" + file_config
    pipeline_command += " | buildkite-agent pipeline upload"

    return """
  - label: \"Setup {0}\"
    command: \"{1}\\n{2}\"
    agents:
      kind: pipeline""".format(project_name, fetch_bazelcipy_command(),
                                    pipeline_command)


def create_label(platform, project_name, build_only=False, test_only=False):
    if build_only and test_only:
        raise BuildkiteException(
            "build_only and test_only cannot be true at the same time")
    platform_name = platforms_info()[platform]["emoji-name"]

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


def bazel_build_step(platform, project_name, http_config=None, file_config=None, build_only=False, test_only=False):
    pipeline_command = python_binary(platform) + " bazelci.py runner"
    if build_only:
        pipeline_command += " --build_only --save_but"
    if test_only:
        pipeline_command += " --test_only"
    if http_config:
        pipeline_command += " --http_config=" + http_config
    if file_config:
        pipeline_command += " --file_config=" + file_config
    label = create_label(platform, project_name, build_only, test_only)
    pipeline_command += " --platform=" + platform

    return """
  - label: \"{0}\"
    command: \"{1}\\n{2}\"
    agents:
      kind: worker
      java: 8
      os: {3}""".format(label, fetch_bazelcipy_command(),
                             pipeline_command, platform)


def publish_bazel_binaries_step():
    command = python_binary() + " bazelci.py publish_binaries"
    return """
  - label: \"Publish Bazel Binaries\"
    command: \"{0}\\n{1}\"
    agents:
      kind: pipeline""".format(fetch_bazelcipy_command(), command)


def print_bazel_publish_binaries_pipeline(configs, http_config, file_config):
    if not configs:
        raise BuildkiteException(
            "Bazel publish binaries pipeline configuration is empty.")
    if set(configs.keys()) != set(supported_platforms()):
        raise BuildkiteException(
            "Bazel publish binaries pipeline needs to build Bazel on all supported platforms.")

    # Build and Test Bazel
    pipeline_steps = []
    for platform, config in configs.items():
        pipeline_steps.append(bazel_build_step(
            platform, "Bazel", http_config, file_config, build_only=True))

    for platform, config in configs.items():
        pipeline_steps.append(bazel_build_step(
            platform, "Bazel", http_config, file_config, test_only=True))

    pipeline_steps.append(wait_step())

    # If all builds and tests pass, publish the Bazel binaries
    # to GCS.
    pipeline_steps.append(publish_bazel_binaries_step())

    print_pipeline(pipeline_steps)


def print_bazel_downstream_pipeline(configs, http_config, file_config):
    if not configs:
        raise BuildkiteException(
            "Bazel downstream pipeline configuration is empty.")
    if set(configs.keys()) != set(supported_platforms()):
        raise BuildkiteException(
            "Bazel downstream pipeline needs to build Bazel on all supported platforms.")

    pipeline_steps = []
    for platform, config in configs.items():
        pipeline_steps.append(bazel_build_step(
            platform, "Bazel", http_config, file_config, build_only=True))
    pipeline_steps.append(wait_step())

    for platform, config in configs.items():
        pipeline_steps.append(bazel_build_step(
            platform, "Bazel", http_config, file_config, test_only=True))

    for project, config in downstream_projects().items():
        git_repository = config["git_repository"]
        pipeline_steps.append(upload_project_pipeline_step(project,
                                                           git_repository, config.get("http_config", None), config.get("file_config", None)))

    print_pipeline(pipeline_steps)


def bazelci_builds_download_url(platform, build_number):
    return "https://storage.googleapis.com/bazel-builds/artifacts/{0}/{1}/bazel".format(platform, build_number)


def bazelci_builds_upload_url(platform, build_number):
    return "gs://bazel-builds/artifacts/{0}/{1}/bazel".format(platform, build_number)


def bazelci_builds_metadata_url():
    return "gs://bazel-builds/metadata/latest.json"


def latest_generation_and_build_number():
    output = None
    attempt = 0
    while attempt < 5:
        output = subprocess.check_output(
            [gsutil_command(), "stat", bazelci_builds_metadata_url()])
        match = re.search("Generation:[ ]*([0-9]+)", output.decode("utf-8"))
        if not match:
            raise BuildkiteException(
                "Couldn't parse generation. gsutil output format changed?")
        generation = match.group(1)

        match = re.search(r"Hash \(md5\):[ ]*([^\s]+)", output.decode("utf-8"))
        if not match:
            raise BuildkiteException(
                "Couldn't parse md5 hash. gsutil output format changed?")
        expected_md5hash = base64.b64decode(match.group(1))

        output = subprocess.check_output(
            [gsutil_command(), "cat", bazelci_builds_metadata_url()])
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
    now = datetime.datetime.now()
    info = {
        "build_number": build_number,
        "build_time": now.strftime("%d-%m-%Y %H:%M"),
        "git_commit": os.environ["BUILDKITE_COMMIT"],
        "platforms": {}
    }
    for platform in supported_platforms():
        tmpdir = tempfile.mkdtemp()
        try:
            bazel_binary_path = download_bazel_binary(tmpdir, platform)
            execute_command([gsutil_command(), "cp", "-a", "public-read", bazel_binary_path,
                             bazelci_builds_upload_url(platform, build_number)])
            info["platforms"][platform] = {
                "url": bazelci_builds_download_url(platform, build_number),
                "sha256": sha256_hexdigest(bazel_binary_path),
            }
        finally:
            shutil.rmtree(tmpdir)
    tmpdir = tempfile.mkdtemp()
    try:
        info_file = os.path.join(tmpdir, "info.json")
        with open(info_file, mode="w", encoding="utf-8") as fp:
            json.dump(info, fp, indent=2, sort_keys=True)

        try:
            execute_command([
                gsutil_command(),
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
        raise BuildkiteException(
            "Could not publish binaries, ran out of attempts.")


def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(
        description='Bazel Continuous Integration Script')

    subparsers = parser.add_subparsers(dest="subparsers_name")

    bazel_publish_binaries_pipeline = subparsers.add_parser("bazel_publish_binaries_pipeline")
    bazel_publish_binaries_pipeline.add_argument("--file_config", type=str)
    bazel_publish_binaries_pipeline.add_argument("--http_config", type=str)
    bazel_publish_binaries_pipeline.add_argument("--git_repository", type=str)

    bazel_downstream_pipeline = subparsers.add_parser("bazel_downstream_pipeline")
    bazel_downstream_pipeline.add_argument("--file_config", type=str)
    bazel_downstream_pipeline.add_argument("--http_config", type=str)
    bazel_downstream_pipeline.add_argument("--git_repository", type=str)

    project_pipeline = subparsers.add_parser("project_pipeline")
    project_pipeline.add_argument("--project_name", type=str)
    project_pipeline.add_argument("--file_config", type=str)
    project_pipeline.add_argument("--http_config", type=str)
    project_pipeline.add_argument("--git_repository", type=str)
    project_pipeline.add_argument(
        "--use_but", type=bool, nargs="?", const=True)

    runner = subparsers.add_parser("runner")
    runner.add_argument("--platform", action="store",
                        choices=list(supported_platforms()))
    runner.add_argument("--file_config", type=str)
    runner.add_argument("--http_config", type=str)
    runner.add_argument("--git_repository", type=str)
    runner.add_argument("--use_but", type=bool, nargs="?", const=True)
    runner.add_argument("--save_but", type=bool, nargs="?", const=True)
    runner.add_argument("--build_only", type=bool, nargs="?", const=True)
    runner.add_argument("--test_only", type=bool, nargs="?", const=True)

    runner = subparsers.add_parser("publish_binaries")

    args = parser.parse_args()

    try:
        if args.subparsers_name == "bazel_publish_binaries_pipeline":
            configs = fetch_configs(args.http_config, args.file_config)
            print_bazel_publish_binaries_pipeline(configs.get("platforms", None), args.http_config, args.file_config)
        elif args.subparsers_name == "bazel_downstream_pipeline":
            configs = fetch_configs(args.http_config, args.file_config)
            print_bazel_downstream_pipeline(
                configs.get("platforms", None), args.http_config, args.file_config)
        elif args.subparsers_name == "project_pipeline":
            configs = fetch_configs(args.http_config, args.file_config)
            print_project_pipeline(configs.get("platforms", None), args.project_name,
                                   args.http_config, args.file_config, args.git_repository, args.use_but)
        elif args.subparsers_name == "runner":
            configs = fetch_configs(args.http_config, args.file_config)
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
