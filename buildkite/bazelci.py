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
import time
import urllib.request
import uuid
import yaml
from github3 import login
from urllib.request import url2pathname
from urllib.parse import urlparse

# Initialize the random number generator.
random.seed()


DOWNSTREAM_PROJECTS = {
    "Android Testing": {
        "git_repository": "https://github.com/googlesamples/android-testing.git",
        "http_config": "https://raw.githubusercontent.com/googlesamples/android-testing/master/bazelci/buildkite-pipeline.yml",
        "pipeline_slug": "android-testing"
    },
    "Bazel Remote Execution": {
        "git_repository": "https://github.com/bazelbuild/bazel.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/bazel-remote-execution-postsubmit.yml",
        "pipeline_slug": "remote-execution"
    },
    "BUILD_file_generator": {
        "git_repository": "https://github.com/bazelbuild/BUILD_file_generator.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/BUILD_file_generator/master/.bazelci/presubmit.yml",
        "pipeline_slug": "build-file-generator",
    },
    "bazel-toolchains": {
        "git_repository": "https://github.com/bazelbuild/bazel-toolchains.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/bazel-toolchains/master/.bazelci/presubmit.yml",
        "pipeline_slug": "bazel-toolchains"
    },
    "bazel-skylib": {
        "git_repository": "https://github.com/bazelbuild/bazel-skylib.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/bazel-skylib/master/.bazelci/presubmit.yml",
        "pipeline_slug": "bazel-skylib"
    },
    "buildtools": {
        "git_repository": "https://github.com/bazelbuild/buildtools.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/buildtools/master/.bazelci/presubmit.yml",
        "pipeline_slug": "buildtools"
    },
    "CLion Plugin": {
        "git_repository": "https://github.com/bazelbuild/intellij.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/clion-postsubmit.yml",
        "pipeline_slug": "clion-plugin"
    },
    "Gerrit": {
        "git_repository": "https://gerrit.googlesource.com/gerrit.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/gerrit-postsubmit.yml",
        "pipeline_slug": "gerrit"
    },
    "Google Logging": {
        "git_repository": "https://github.com/google/glog.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/glog-postsubmit.yml",
        "pipeline_slug": "google-logging"
    },
    "IntelliJ Plugin": {
        "git_repository": "https://github.com/bazelbuild/intellij.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/intellij-postsubmit.yml",
        "pipeline_slug": "intellij-plugin"
    },
    "migration-tooling": {
        "git_repository": "https://github.com/bazelbuild/migration-tooling.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/migration-tooling/master/.bazelci/presubmit.yml",
        "pipeline_slug": "migration-tooling"
    },
    "protobuf": {
        "git_repository": "https://github.com/google/protobuf.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/protobuf-postsubmit.yml",
        "pipeline_slug": "protobuf"
    },
    "re2": {
        "git_repository": "https://github.com/google/re2.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/re2-postsubmit.yml",
        "pipeline_slug": "re2"
    },
    "rules_appengine": {
        "git_repository": "https://github.com/bazelbuild/rules_appengine.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_appengine/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-appengine-appengine"
    },
    "rules_apple": {
        "git_repository": "https://github.com/bazelbuild/rules_apple.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_apple/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-apple-darwin"
    },
    "rules_closure": {
        "git_repository": "https://github.com/bazelbuild/rules_closure.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_closure/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-closure-closure-compiler"
    },
    "rules_docker": {
        "git_repository": "https://github.com/bazelbuild/rules_docker.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_docker/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-docker-docker",
    },
    "rules_foreign_cc": {
        "git_repository": "https://github.com/bazelbuild/rules_foreign_cc.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_foreign_cc/master/.bazelci/config.yaml",
        "pipeline_slug": "rules-foreign-cc",
    },
    "rules_go": {
        "git_repository": "https://github.com/bazelbuild/rules_go.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_go/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-go-golang"
    },
    "rules_groovy": {
        "git_repository": "https://github.com/bazelbuild/rules_groovy.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_groovy/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-groovy"
    },
    "rules_gwt": {
        "git_repository": "https://github.com/bazelbuild/rules_gwt.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_gwt/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-gwt"
    },
    "rules_jsonnet": {
        "git_repository": "https://github.com/bazelbuild/rules_jsonnet.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_jsonnet/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-jsonnet"
    },
    "rules_kotlin": {
        "git_repository": "https://github.com/bazelbuild/rules_kotlin.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_kotlin/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-kotlin-kotlin"
    },
    "rules_k8s": {
        "git_repository": "https://github.com/bazelbuild/rules_k8s.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_k8s/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-k8s-k8s"
    },
    "rules_nodejs": {
        "git_repository": "https://github.com/bazelbuild/rules_nodejs.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_nodejs/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-nodejs-nodejs"
    },
    "rules_perl": {
        "git_repository": "https://github.com/bazelbuild/rules_perl.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_perl/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-perl"
    },
    "rules_python": {
        "git_repository": "https://github.com/bazelbuild/rules_python.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_python/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-python-python"
    },
    "rules_rust": {
        "git_repository": "https://github.com/bazelbuild/rules_rust.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_rust/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-rust-rustlang"
    },
    "rules_sass": {
        "git_repository": "https://github.com/bazelbuild/rules_sass.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_sass/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-sass"
    },
    "rules_scala": {
        "git_repository": "https://github.com/bazelbuild/rules_scala.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_scala/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-scala-scala"
    },
    "rules_typescript": {
        "git_repository": "https://github.com/bazelbuild/rules_typescript.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_typescript/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-typescript-typescript",
        "disabled_reason": "Re-enable once merged: https://github.com/bazelbuild/rules_typescript/pull/343"
    },
    "rules_webtesting": {
        "git_repository": "https://github.com/bazelbuild/rules_webtesting.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_webtesting-postsubmit.yml",
        "pipeline_slug": "rules-webtesting-saucelabs",
        "disabled_reason": "Re-enable once fixed: https://github.com/bazelbuild/continuous-integration/issues/191"
    },
    "skydoc": {
        "git_repository": "https://github.com/bazelbuild/skydoc.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/skydoc/master/.bazelci/presubmit.yml",
        "pipeline_slug": "skydoc"
    },
    "subpar": {
        "git_repository": "https://github.com/google/subpar.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/subpar-postsubmit.yml",
        "pipeline_slug": "subpar"
    },
    "TensorFlow": {
        "git_repository": "https://github.com/tensorflow/tensorflow.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/tensorflow-postsubmit.yml",
        "pipeline_slug": "tensorflow"
    }
}


# A map containing all supported platform names as keys, with the values being
# the platform name in a human readable format, and a the buildkite-agent's
# working directory.
PLATFORMS = {
    "ubuntu1404": {
        "name": "Ubuntu 14.04, JDK 8",
        "emoji-name": ":ubuntu: 14.04 (JDK 8)",
        "agent-directory": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}",
        "publish_binary": True,
        "java": "8"
    },
    "ubuntu1604": {
        "name": "Ubuntu 16.04, JDK 8",
        "emoji-name": ":ubuntu: 16.04 (JDK 8)",
        "agent-directory": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}",
        "publish_binary": False,
        "java": "8"
    },
    "ubuntu1804": {
        "name": "Ubuntu 18.04, JDK 8",
        "emoji-name": ":ubuntu: 18.04 (JDK 8)",
        "agent-directory": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}",
        "publish_binary": False,
        "java": "8"
    },
    "ubuntu1804_nojava": {
        "name": "Ubuntu 18.04, no JDK",
        "emoji-name": ":ubuntu: 18.04 (no JDK)",
        "agent-directory": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}",
        "publish_binary": False,
        "java": "no"
    },
    "ubuntu1804_java9": {
        "name": "Ubuntu 18.04, JDK 9",
        "emoji-name": ":ubuntu: 18.04 (JDK 9)",
        "agent-directory": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}",
        "publish_binary": False,
        "java": "9"
    },
    "ubuntu1804_java10": {
        "name": "Ubuntu 18.04, JDK 10",
        "emoji-name": ":ubuntu: 18.04 (JDK 10)",
        "agent-directory": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}",
        "publish_binary": False,
        "java": "10"
    },
    "macos": {
        "name": "macOS, JDK 8",
        "emoji-name": ":darwin: (JDK 8)",
        "agent-directory": "/Users/buildkite/builds/${BUILDKITE_AGENT_NAME}",
        "publish_binary": True,
        "java": "8"
    },
    "windows": {
        "name": "Windows, JDK 8",
        "emoji-name": ":windows: (JDK 8)",
        "agent-directory": "d:/b/${BUILDKITE_AGENT_NAME}",
        "publish_binary": True,
        "java": "8"
    },
    "rbe_ubuntu1604": {
        "name": "RBE (Ubuntu 16.04, JDK 8)",
        "emoji-name": ":gcloud: (JDK 8)",
        "agent-directory": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}",
        "publish_binary": False,
        "host-platform": "ubuntu1604",
        "java": "8"
    }
}

# A list of incompatible flags to be tested in downstream with the latest release Bazel
INCOMPATIBLE_FLAGS = {
    "--incompatible_use_jdk10_as_host_javabase" : "https://github.com/bazelbuild/bazel/issues/6661",
    "--incompatible_disallow_data_transition" : "https://github.com/bazelbuild/bazel/issues/6153",
}


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


def rchop(string_, *endings):
    for ending in endings:
        if string_.endswith(ending):
            return string_[:-len(ending)]
    return string_

def python_binary(platform=None):
    if platform == "windows":
        return "python.exe"
    if platform == "macos":
        return "python3.7"
    return "python3.6"


def is_windows():
    return os.name == "nt"


def gsutil_command():
    return "gsutil.cmd" if is_windows() else "gsutil"


def gcloud_command():
    return "gcloud.cmd" if is_windows() else "gcloud"


def bazelcipy_url():
    """
    URL to the latest version of this script.
    """
    return "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?{}".format(int(time.time()))


def incompatible_flag_verbose_failures_url():
    """
    URL to the latest version of this script.
    """
    return "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/incompatible_flag_verbose_failures.py?{}".format(int(time.time()))


def downstream_projects_root(platform):
    downstream_projects_dir = os.path.expandvars("${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects")
    agent_directory = os.path.expandvars(PLATFORMS[platform]["agent-directory"])
    path = os.path.join(agent_directory, downstream_projects_dir)
    if not os.path.exists(path):
        os.makedirs(path)
    return path


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


def execute_commands(config, platform, git_repository, git_commit, git_repo_location,
                     use_bazel_at_commit, use_but, save_but, build_only, test_only,
                     monitor_flaky_tests, incompatible_flags):
    fail_pipeline = False
    tmpdir = None
    bazel_binary = "bazel"
    commit = os.getenv("BUILDKITE_COMMIT")
    build_only = build_only or "test_targets" not in config
    test_only = test_only or "build_targets" not in config
    if build_only and test_only:
        raise BuildkiteException("build_only and test_only cannot be true at the same time")

    if use_bazel_at_commit and use_but:
        raise BuildkiteException("use_bazel_at_commit cannot be set when use_but is true")

    tmpdir = tempfile.mkdtemp()
    sc_process = None
    try:
        if git_repo_location:
            os.chdir(git_repo_location)
        elif git_repository:
            clone_git_repository(git_repository, platform, git_commit)
        else:
            git_repository = os.getenv("BUILDKITE_REPO")

        if (is_pull_request()
                and not os.getenv("BUILDKITE_PULL_REQUEST_REPO").startswith("git://github.com/bazelbuild/")
                and not is_trusted_author(github_user_for_pull_request(), git_repository)):
            update_pull_request_verification_status(git_repository, commit, state="success")

        if use_bazel_at_commit:
            print_collapsed_group(":gcloud: Downloading Bazel built at " + use_bazel_at_commit)
            bazel_binary = download_bazel_binary_at_commit(tmpdir, platform, use_bazel_at_commit)

        if use_but:
            print_collapsed_group(":gcloud: Downloading Bazel Under Test")
            bazel_binary = download_bazel_binary(tmpdir, platform)

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
        execute_bazel_run(bazel_binary, platform, config.get("run_targets", None), incompatible_flags)

        if config.get("sauce", None):
            print_collapsed_group(":saucelabs: Starting Sauce Connect Proxy")
            os.environ["SAUCE_USERNAME"] = "bazel_rules_webtesting"
            os.environ["SAUCE_ACCESS_KEY"] = fetch_saucelabs_token()
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
                    raise BuildkiteException("Sauce Connect Proxy is still not ready after 30 seconds, aborting!")
                time.sleep(1)
            print("Sauce Connect Proxy is ready, continuing...")

        if not test_only:
            build_bep_file = os.path.join(tmpdir, "build_bep.json")
            if is_pull_request():
                update_pull_request_build_status(
                    platform, git_repository, commit, "pending", None)
            try:
                execute_bazel_build(bazel_binary, platform, config.get("build_flags", []),
                                    config.get("build_targets", None), build_bep_file, incompatible_flags)
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
                                   config.get("test_targets", None), test_bep_file,
                                   monitor_flaky_tests, incompatible_flags)
                if has_flaky_tests(test_bep_file):
                    if monitor_flaky_tests:
                        # Upload the BEP logs from Bazel builds for later analysis on flaky tests
                        build_id = os.getenv("BUILDKITE_BUILD_ID")
                        pipeline_slug = os.getenv("BUILDKITE_PIPELINE_SLUG")
                        execute_command([gsutil_command(), "cp", test_bep_file,
                            "gs://bazel-buildkite-stats/flaky-tests-bep/" + pipeline_slug + "/" + build_id + ".json"])
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
        if sc_process:
            sc_process.terminate()
            try:
                sc_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                sc_process.kill()
        if tmpdir:
            shutil.rmtree(tmpdir)

    if fail_pipeline:
        raise BuildkiteException("At least one test failed or was flaky.")


def tests_with_status(bep_file, status):
    return set(label for label, _ in test_logs_for_status(bep_file, status=status))


__github_token__ = None
__saucelabs_token__ = None
__buildkite_token__ = None


def fetch_github_token():
    global __github_token__
    if __github_token__:
        return __github_token__
    try:
        execute_command(
            [gsutil_command(), "cp", "gs://bazel-encrypted-secrets/github-token.enc", "github-token.enc"])
        __github_token__ = subprocess.check_output([gcloud_command(), "kms", "decrypt", "--location", "global", "--keyring", "buildkite",
                                                    "--key", "github-token", "--ciphertext-file", "github-token.enc",
                                                    "--plaintext-file", "-"], env=os.environ).decode("utf-8").strip()
        return __github_token__
    finally:
        os.remove("github-token.enc")


def fetch_saucelabs_token():
    global __saucelabs_token__
    if __saucelabs_token__:
        return __saucelabs_token__
    try:
        execute_command(
            [gsutil_command(), "cp", "gs://bazel-encrypted-secrets/saucelabs-access-key.enc", "saucelabs-access-key.enc"])
        __saucelabs_token__ = subprocess.check_output([gcloud_command(), "kms", "decrypt", "--location", "global", "--keyring", "buildkite",
                                                       "--key", "saucelabs-access-key", "--ciphertext-file", "saucelabs-access-key.enc",
                                                       "--plaintext-file", "-"], env=os.environ).decode("utf-8").strip()
        return __saucelabs_token__
    finally:
        os.remove("saucelabs-access-key.enc")


def fetch_buildkite_token():    
    global __buildkite_token__
    if __buildkite_token__:
        return __buildkite_token__
    try:
        execute_command(
            [gsutil_command(), "cp", "gs://bazel-encrypted-secrets/buildkite-api-token.enc", "buildkite-api-token.enc"])
        __buildkite_token__ = subprocess.check_output([gcloud_command(), "kms", "decrypt", "--location", "global", "--keyring", "buildkite",
                                                       "--key", "buildkite-api-token", "--ciphertext-file", "buildkite-api-token.enc",
                                                       "--plaintext-file", "-"], env=os.environ).decode("utf-8").strip()
        return __buildkite_token__
    finally:
        os.remove("buildkite-api-token.enc")


def owner_repository_from_url(git_repository):
    m = re.search(r"/([^/]+)/([^/]+)\.git$", git_repository)
    owner = m.group(1)
    repository = m.group(2)
    return (owner, repository)


def results_view_url(invocation_id):
    if invocation_id:
        return "https://source.cloud.google.com/results/invocations/" + invocation_id
    return None


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
    update_pull_request_status(git_repository, commit, state, results_view_url(invocation_id),
                               description, "bazel build ({0})".format(PLATFORMS[platform]["name"]))


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
    update_pull_request_status(git_repository, commit, state, results_view_url(invocation_id),
                               description, "bazel test ({0})".format(PLATFORMS[platform]["name"]))


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


def has_flaky_tests(bep_file):
    return len(test_logs_for_status(bep_file, status="FLAKY")) > 0


def print_bazel_version_info(bazel_binary, platform):
    print_collapsed_group(":information_source: Bazel Info")
    execute_command([bazel_binary] + common_startup_flags(platform) + ["--nomaster_bazelrc", "--bazelrc=/dev/null", "version"])
    execute_command([bazel_binary] + common_startup_flags(platform) + ["--nomaster_bazelrc", "--bazelrc=/dev/null", "info"])


def print_environment_variables_info():
    print_collapsed_group(":information_source: Environment Variables")
    for key, value in os.environ.items():
        eprint("%s=(%s)" % (key, value))


def upload_bazel_binary(platform):
    print_collapsed_group(":gcloud: Uploading Bazel Under Test")
    binary_path = "bazel-bin/src/bazel_jdk_minimal"
    if platform == "windows":
        binary_path = r"bazel-bin\src\bazel_jdk_minimal"
    execute_command(["buildkite-agent", "artifact", "upload", binary_path])


def download_bazel_binary(dest_dir, platform):
    host_platform = PLATFORMS[platform].get("host-platform", platform)
    binary_path = "bazel-bin/src/bazel_jdk_minimal"
    if platform == "windows":
        binary_path = r"bazel-bin\src\bazel_jdk_minimal"

    source_step = create_label(host_platform, "Bazel", build_only=True)
    execute_command(["buildkite-agent", "artifact", "download",
                     binary_path, dest_dir, "--step", source_step])
    bazel_binary_path = os.path.join(dest_dir, binary_path)
    st = os.stat(bazel_binary_path)
    os.chmod(bazel_binary_path, st.st_mode | stat.S_IEXEC)
    return bazel_binary_path


def download_bazel_binary_at_commit(dest_dir, platform, bazel_git_commit):
    # We only build bazel binary on ubuntu14.04 for every bazel commit.
    # It should be OK to use it on other ubuntu platforms.
    if "ubuntu" in PLATFORMS[platform].get("host-platform", platform):
        platform = "ubuntu1404"
    bazel_binary_path = os.path.join(dest_dir, "bazel.exe" if platform == "windows" else "bazel")
    execute_command([gsutil_command(), "cp", bazelci_builds_gs_url(platform, bazel_git_commit),
                     bazel_binary_path])
    st = os.stat(bazel_binary_path)
    os.chmod(bazel_binary_path, st.st_mode | stat.S_IEXEC)
    return bazel_binary_path

def clone_git_repository(git_repository, platform, git_commit=None):
    root = downstream_projects_root(platform)
    project_name = re.search(r"/([^/]+)\.git$", git_repository).group(1)
    clone_path = os.path.join(root, project_name)
    print_collapsed_group("Fetching %s sources at %s" % (project_name, git_commit if git_commit else "HEAD"))

    if not os.path.exists(clone_path):
        if platform in ["ubuntu1404", "ubuntu1604", "ubuntu1804", "rbe_ubuntu1604"]:
            execute_command(["git", "clone", "--reference", "/var/lib/bazelbuild", git_repository, clone_path])
        elif platform in ["macos"]:
            execute_command(["git", "clone", "--reference", "/usr/local/var/bazelbuild", git_repository, clone_path])
        elif platform in ["windows"]:
            execute_command(["git", "clone", "--reference", "c:\\buildkite\\bazelbuild", git_repository, clone_path])
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
        remote_head = subprocess.check_output(["git", "symbolic-ref", "refs/remotes/origin/HEAD"]).decode("utf-8").rstrip()
        execute_command(["git", "reset", remote_head, "--hard"])
    execute_command(["git", "submodule", "sync", "--recursive"])
    execute_command(["git", "submodule", "update", "--init", "--recursive", "--force"])
    execute_command(["git", "submodule", "foreach", "--recursive", "git", "reset", "--hard"])
    execute_command(["git", "clean", "-fdqx"])
    execute_command(["git", "submodule", "foreach", "--recursive", "git", "clean", "-fdqx"])
    return clone_path


def execute_batch_commands(commands):
    if not commands:
        return
    print_collapsed_group(":batch: Setup (Batch Commands)")
    batch_commands = "&".join(commands)
    return subprocess.run(batch_commands, shell=True, check=True, env=os.environ).returncode


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
        execute_command([bazel_binary] + common_startup_flags(platform) + ["run"] + common_build_flags(None, platform) + (incompatible_flags or []) + [target])


def remote_caching_flags(platform):
    if platform not in ["ubuntu1404", "ubuntu1604", "ubuntu1804", "ubuntu1804_nojava", "ubuntu1804_java9", "ubuntu1804_java10", "macos"]:
        return []
    flags = ["--google_default_credentials", "--experimental_guard_against_concurrent_changes"]
    if is_pull_request():
        flags += ["--bes_backend=buildeventservice.googleapis.com",
                  "--bes_timeout=360s",
                  "--tls_enabled",
                  "--project_id=bazel-public",
                  "--remote_instance_name=projects/bazel-public/instances/default_instance",
                  # TODO(ulfjack): figure out how to resolve
                  # https://github.com/bazelbuild/bazel/issues/5382 and as part of that keep
                  # or remove the `--disk_cache=` flag.
                  "--disk_cache=",
                  "--remote_timeout=360",
                  "--remote_cache=remotebuildexecution.googleapis.com",
                  "--experimental_remote_platform_override=properties:{name:\"platform\" value:\"" + platform + "\"}"]
    else:
        flags += ["--remote_timeout=10",
                  # TODO(ulfjack): figure out how to resolve
                  # https://github.com/bazelbuild/bazel/issues/5382 and as part of that keep
                  # or remove the `--disk_cache=` flag.
                  "--disk_cache=",
                  "--remote_max_connections=200",
                  "--experimental_remote_platform_override=properties:{name:\"platform\" value:\"" + platform + "\"}",
                  "--remote_http_cache=https://storage.googleapis.com/bazel-buildkite-cache"]
    return flags


def remote_enabled(flags):
    # Detect if the project configuration enabled its own remote caching / execution.
    remote_flags = ["--remote_executor", "--remote_cache", "--remote_http_cache"]
    for flag in flags:
        for remote_flag in remote_flags:
            if flag.startswith(remote_flag):
                return True
    return False


def concurrent_jobs(platform):
    return "75" if platform.startswith("rbe_") else str(multiprocessing.cpu_count())


def concurrent_test_jobs(platform):
    if platform.startswith("rbe_"):
        return "75"
    elif platform == "windows":
        return "8"
    elif platform == "macos":
        return "8"
    return "12"


def common_startup_flags(platform):
    flags = []
    if platform == "windows":
        flags += ["--output_user_root=D:/b"]
    return flags


def common_build_flags(bep_file, platform):
    flags = [
        "--show_progress_rate_limit=5",
        "--curses=yes",
        "--color=yes",
        "--verbose_failures",
        "--keep_going",
        "--jobs=" + concurrent_jobs(platform),
        "--experimental_build_event_json_file_path_conversion=false",
        "--announce_rc",
        "--sandbox_tmpfs_path=/tmp",
        "--experimental_multi_threaded_digest"
    ]
    if bep_file:
        flags += ["--build_event_json_file=" + bep_file]
    return flags


def rbe_flags(original_flags, accept_cached):
    # Enable remote execution via RBE.
    flags = [
        "--remote_executor=remotebuildexecution.googleapis.com",
        "--remote_instance_name=projects/bazel-public/instances/default_instance",
        "--remote_timeout=3600",
        "--spawn_strategy=remote",
        "--strategy=Javac=remote",
        "--strategy=Closure=remote",
        "--genrule_strategy=remote",
        "--experimental_strict_action_env",
        "--tls_enabled=true",
        "--google_default_credentials"
    ]

    # Enable BES / Build Results reporting.
    flags += [
        "--bes_backend=buildeventservice.googleapis.com",
        "--bes_timeout=360s",
        "--project_id=bazel-public"
    ]

    if not accept_cached:
        flags += ["--noremote_accept_cached"]

    # Copied from https://github.com/bazelbuild/bazel-toolchains/blob/master/configs/ubuntu16_04_clang/1.0/toolchain.bazelrc
    flags += [
        # These should NOT be modified before @bazel_toolchains repo pin is
        # updated in projects' WORKSPACE files.
        #
        # Toolchain related flags to append at the end of your .bazelrc file.
        "--host_javabase=@bazel_toolchains//configs/ubuntu16_04_clang/latest:javabase",
        "--javabase=@bazel_toolchains//configs/ubuntu16_04_clang/latest:javabase",
        "--host_java_toolchain=@bazel_tools//tools/jdk:toolchain_hostjdk8",
        "--java_toolchain=@bazel_tools//tools/jdk:toolchain_hostjdk8",
        "--crosstool_top=@bazel_toolchains//configs/ubuntu16_04_clang/latest:crosstool_top_default",
        "--action_env=BAZEL_DO_NOT_DETECT_CPP_TOOLCHAIN=1",
    ]

    # Platform flags:
    # The toolchain container used for execution is defined in the target indicated
    # by "extra_execution_platforms", "host_platform" and "platforms".
    # If you are using your own toolchain container, you need to create a platform
    # target with "constraint_values" that allow for the toolchain specified with
    # "extra_toolchains" to be selected (given constraints defined in
    # "exec_compatible_with").
    # More about platforms: https://docs.bazel.build/versions/master/platforms.html
    # Don't add platform flags if they are specified already.
    platform_flags = {
        "--extra_toolchains" : "@bazel_toolchains//configs/ubuntu16_04_clang/latest:toolchain_default",
        "--extra_execution_platforms" : "@bazel_toolchains//configs/ubuntu16_04_clang/latest:platform",
        "--host_platform" : "@bazel_toolchains//configs/ubuntu16_04_clang/latest:platform",
        "--platforms" : "@bazel_toolchains//configs/ubuntu16_04_clang/latest:platform",
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

    aggregated_flags = compute_flags(platform, flags, incompatible_flags, bep_file, enable_remote_cache=True)
    try:
        execute_command([bazel_binary] + common_startup_flags(platform) + ["build"] + aggregated_flags + targets)
    except subprocess.CalledProcessError as e:
        raise BazelBuildFailedException(
            "bazel build failed with exit code {}".format(e.returncode))


def execute_bazel_test(bazel_binary, platform, flags, targets, bep_file, monitor_flaky_tests, incompatible_flags):
    print_expanded_group(":bazel: Test")

    aggregated_flags = ["--flaky_test_attempts=3",
                        "--build_tests_only",
                        "--local_test_jobs=" + concurrent_test_jobs(platform)]
    # Don't enable remote caching if the user enabled remote execution / caching themselves
    # or flaky test monitoring is enabled, as remote caching makes tests look less flaky than
    # they are.
    aggregated_flags += compute_flags(platform,
                                      flags,
                                      incompatible_flags,
                                      bep_file,
                                      enable_remote_cache=not monitor_flaky_tests)

    try:
        execute_command([bazel_binary] + common_startup_flags(platform) + ["test"] + aggregated_flags + targets)
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
    return subprocess.run(args, shell=shell, check=fail_if_nonzero, env=os.environ).returncode


def execute_command_background(args):
    eprint(" ".join(args))
    #return subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=os.environ)
    return subprocess.Popen(args, env=os.environ)


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
                           git_repository, monitor_flaky_tests, use_but, incompatible_flags):
    if not platform_configs:
        raise BuildkiteException("{0} pipeline configuration is empty.".format(project_name))

    pipeline_steps = []
    if is_pull_request():
        commit_author = github_user_for_pull_request()
        trusted_git_repository = git_repository or os.getenv("BUILDKITE_REPO")
        if (is_pull_request()
                and not os.getenv("BUILDKITE_PULL_REQUEST_REPO").startswith("git://github.com/bazelbuild/")
                and not is_trusted_author(commit_author, trusted_git_repository)):
            commit = os.getenv("BUILDKITE_COMMIT")
            update_pull_request_verification_status(trusted_git_repository, commit, state="pending")
            pipeline_steps.append({
                "block": "Verify Pull Request",
                "prompt": "Did you review this pull request for malicious code?"
            })

    # In Bazel Downstream Project pipelines, git_repository and project_name must be specified,
    # and we should test the project at the last green commit.
    git_commit = None
    if (use_but or incompatible_flags) and git_repository and project_name:
        git_commit = get_last_green_commit(git_repository, DOWNSTREAM_PROJECTS[project_name]["pipeline_slug"])
    for platform in platform_configs:
        step = runner_step(platform, project_name, http_config, file_config,
                           git_repository, git_commit, monitor_flaky_tests, use_but, incompatible_flags)
        pipeline_steps.append(step)

    pipeline_slug = os.getenv("BUILDKITE_PIPELINE_SLUG")
    all_downstream_pipeline_slugs = []
    for _, config in DOWNSTREAM_PROJECTS.items():
        all_downstream_pipeline_slugs.append(config["pipeline_slug"])
    # We don't need to update last green commit in the following cases:
    #   1. This job is a github pull request
    #   2. This job uses a custom built Bazel binary (In Bazel Downstream Projects pipeline)
    #   3. This job doesn't run on master branch (Could be a custom build launched manually)
    #   4. We don't intend to run the same job in downstream with Bazel@HEAD (eg. google-bazel-presubmit)
    #   5. We are testing incompatible flags
    if not (is_pull_request() or use_but or os.getenv("BUILDKITE_BRANCH") != "master" or \
       pipeline_slug not in all_downstream_pipeline_slugs or incompatible_flags):
        pipeline_steps.append("wait")

        # If all builds succeed, update the last green commit of this project
        pipeline_steps.append({
            "label": "Try Update Last Green Commit",
            "command": [
                fetch_bazelcipy_command(),
                python_binary() + " bazelci.py try_update_last_green_commit"
            ],
            "agents": {
                "kind": "pipeline"
            }
        })

    print(yaml.dump({"steps": pipeline_steps}))

def runner_step(platform, project_name=None, http_config=None, file_config=None,
                git_repository=None, git_commit=None, monitor_flaky_tests=False, use_but=False, incompatible_flags=None):
    host_platform = PLATFORMS[platform].get("host-platform", platform)
    command = python_binary(host_platform) + " bazelci.py runner --platform=" + platform
    if http_config:
        command += " --http_config=" + http_config
    if file_config:
        command += " --file_config=" + file_config
    if git_repository:
        command += " --git_repository=" + git_repository
    if git_commit:
        command += " --git_commit=" + git_commit
    if monitor_flaky_tests:
        command += " --monitor_flaky_tests"
    if use_but:
        command += " --use_but"
    for flag in (incompatible_flags or []):
        command += " --incompatible_flag=" + flag
    label = create_label(platform, project_name)
    return {
        "label": label,
        "command": [
            fetch_bazelcipy_command(),
            command
        ],
        "agents": {
            "kind": "worker",
            "java": PLATFORMS[platform]["java"],
            "os": rchop(host_platform, "_nojava", "_java8", "_java9", "_java10")
        }
    }


def fetch_bazelcipy_command():
    return "curl -s {0} -o bazelci.py".format(bazelcipy_url())

def fetch_incompatible_flag_verbose_failures_command():
    return "curl -s {0} -o incompatible_flag_verbose_failures.py".format(incompatible_flag_verbose_failures_url())


def upload_project_pipeline_step(project_name, git_repository, http_config, file_config, incompatible_flags):
    pipeline_command = ("{0} bazelci.py project_pipeline --project_name=\"{1}\" " +
                        "--git_repository={2}").format(python_binary(), project_name,
                                                                 git_repository)
    if incompatible_flags == None:
        pipeline_command += " --use_but"
    else:
        for flag in incompatible_flags:
            pipeline_command += " --incompatible_flag=" + flag
    if http_config:
        pipeline_command += " --http_config=" + http_config
    if file_config:
        pipeline_command += " --file_config=" + file_config
    pipeline_command += " | buildkite-agent pipeline upload"

    return {
        "label": "Setup {0}".format(project_name),
        "command": [
            fetch_bazelcipy_command(),
            pipeline_command
        ],
        "agents": {
            "kind": "pipeline"
        }
    }

def create_label(platform, project_name, build_only=False, test_only=False):
    if build_only and test_only:
        raise BuildkiteException(
            "build_only and test_only cannot be true at the same time")
    platform_name = PLATFORMS[platform]["emoji-name"]

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
    host_platform = PLATFORMS[platform].get("host-platform", platform)
    pipeline_command = python_binary(host_platform) + " bazelci.py runner"
    if build_only:
        pipeline_command += " --build_only"
        if "host-platform" not in PLATFORMS[platform]:
            pipeline_command += " --save_but"
    if test_only:
        pipeline_command += " --test_only"
    if http_config:
        pipeline_command += " --http_config=" + http_config
    if file_config:
        pipeline_command += " --file_config=" + file_config
    pipeline_command += " --platform=" + platform

    return {
        "label": create_label(platform, project_name, build_only, test_only),
        "command": [
            fetch_bazelcipy_command(),
            pipeline_command
        ],
        "agents": {
            "kind": "worker",
            "java": PLATFORMS[platform]["java"],
            "os": rchop(host_platform, "_nojava", "_java8", "_java9", "_java10")
        }
    }


def print_bazel_publish_binaries_pipeline(configs, http_config, file_config):
    if not configs:
        raise BuildkiteException("Bazel publish binaries pipeline configuration is empty.")

    for platform in configs.copy():
        if not platform in PLATFORMS:
            raise BuildkiteException("Unknown platform '{}'".format(platform))
        if not PLATFORMS[platform]["publish_binary"]:
            del configs[platform]

    if set(configs) != set(name for name, platform in PLATFORMS.items() if platform["publish_binary"]):
        raise BuildkiteException("Bazel publish binaries pipeline needs to build Bazel for every commit on all publish_binary-enabled platforms.")

    # Build Bazel
    pipeline_steps = []

    for platform in configs:
        pipeline_steps.append(bazel_build_step(
            platform, "Bazel", http_config, file_config, build_only=True))

    pipeline_steps.append("wait")

    # If all builds succeed, publish the Bazel binaries to GCS.
    pipeline_steps.append({
        "label": "Publish Bazel Binaries",
        "command": [
            fetch_bazelcipy_command(),
            python_binary() + " bazelci.py publish_binaries"
        ],
        "agents": {
            "kind": "pipeline"
        }
    })

    print(yaml.dump({"steps": pipeline_steps}))


def print_disabled_projects_info_box_step():
    info_text = ["Downstream testing is disabled for the following projects :sadpanda:"]
    for project, config in DOWNSTREAM_PROJECTS.items():
        disabled_reason = config.get("disabled_reason", None)
        if disabled_reason:
            info_text.append("* **%s**: %s" % (project, disabled_reason))

    if len(info_text) == 1:
        return None
    return {
        "label": ":sadpanda:",
        "command": [
            "buildkite-agent annotate --style=info \"" + "\n".join(info_text) + "\"",
        ],
        "agents": {
            "kind": "pipeline"
        }
    }

def print_bazel_downstream_pipeline(configs, http_config, file_config, test_incompatible_flags, test_disabled_projects):
    if not configs:
        raise BuildkiteException("Bazel downstream pipeline configuration is empty.")

    if set(configs) != set(PLATFORMS):
        raise BuildkiteException("Bazel downstream pipeline needs to build Bazel on all supported platforms (has=%s vs. want=%s)." % (sorted(set(configs)), sorted(set(PLATFORMS))))

    pipeline_steps = []

    info_box_step = print_disabled_projects_info_box_step()
    if info_box_step is not None:
        pipeline_steps.append(info_box_step)

    for platform in configs:
        pipeline_steps.append(
            bazel_build_step(platform, "Bazel", http_config, file_config, build_only=True))

    pipeline_steps.append("wait")

    incompatible_flags = None
    if test_incompatible_flags:
        incompatible_flags = list(INCOMPATIBLE_FLAGS.keys())
        print_expanded_group("Build and test with the following incompatible flags:")
        for flag in incompatible_flags:
            eprint("%s (%s)\n" % (flag, INCOMPATIBLE_FLAGS[flag]))

    for project, config in DOWNSTREAM_PROJECTS.items():
        disabled_reason = config.get("disabled_reason", None)
        # If test_disabled_projects is true, we add configs for disabled projects.
        # If test_disabled_projects is false, we add configs for not disbaled projects.
        if (test_disabled_projects and disabled_reason) or (not test_disabled_projects and not disabled_reason):
            pipeline_steps.append(
                upload_project_pipeline_step(project_name=project,
                                             git_repository=config["git_repository"],
                                             http_config=config.get("http_config", None),
                                             file_config=config.get("file_config", None),
                                             incompatible_flags=incompatible_flags))

    if test_incompatible_flags:
        pipeline_steps.append({
            "wait": "~",
            "continue_on_failure": "true"
        })
        current_build_number = os.environ.get("BUILDKITE_BUILD_NUMBER", None)
        if not current_build_number:
            raise BuildkiteException("Not running inside Buildkite")
        pipeline_steps.append({
            "label": "Test failing jobs with incompatible flag separately",
            "command": [
                fetch_bazelcipy_command(),
                fetch_incompatible_flag_verbose_failures_command(),
                python_binary() + " incompatible_flag_verbose_failures.py --build_number=%s | buildkite-agent pipeline upload" % current_build_number,
            ],
            "agents": {
                "kind": "pipeline"
            }
        })

    print(yaml.dump({"steps": pipeline_steps}))


def bazelci_builds_download_url(platform, git_commit):
    return "https://storage.googleapis.com/bazel-builds/artifacts/{0}/{1}/bazel".format(platform, git_commit)


def bazelci_builds_gs_url(platform, git_commit):
    return "gs://bazel-builds/artifacts/{0}/{1}/bazel".format(platform, git_commit)


def bazelci_builds_metadata_url():
    return "gs://bazel-builds/metadata/latest.json"


def bazelci_last_green_commit_url(git_repository, pipeline_slug):
    return "gs://bazel-builds/last_green_commit/%s/%s" % (git_repository[len("https://"):], pipeline_slug)


def get_last_green_commit(git_repository, pipeline_slug):
    last_green_commit_url = bazelci_last_green_commit_url(git_repository, pipeline_slug)
    try:
        return subprocess.check_output([gsutil_command(), "cat", last_green_commit_url], env=os.environ).decode("utf-8").strip()
    except subprocess.CalledProcessError:
        return None


def try_update_last_green_commit():
    pipeline_slug = os.getenv("BUILDKITE_PIPELINE_SLUG")
    git_repository = os.getenv("BUILDKITE_REPO")
    last_green_commit = get_last_green_commit(git_repository, pipeline_slug)
    current_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    if last_green_commit:
        result = subprocess.check_output(["git", "rev-list", "%s..%s" % (last_green_commit, current_commit)]).decode("utf-8").strip()

    # If current_commit is newer that last_green_commit, `git rev-list A..B` will output a bunch of commits,
    # otherwise the output should be empty.
    if not last_green_commit or result:
        execute_command(["echo %s | %s cp - %s" % (current_commit, gsutil_command(), bazelci_last_green_commit_url(git_repository, pipeline_slug))], shell = True)
    else:
        eprint("Updating abandoned: last green commit (%s) is not older than current commit (%s)." % (last_green_commit, current_commit))

def latest_generation_and_build_number():
    output = None
    attempt = 0
    while attempt < 5:
        output = subprocess.check_output(
            [gsutil_command(), "stat", bazelci_builds_metadata_url()], env=os.environ)
        match = re.search("Generation:[ ]*([0-9]+)", output.decode("utf-8"))
        if not match:
            raise BuildkiteException("Couldn't parse generation. gsutil output format changed?")
        generation = match.group(1)

        match = re.search(r"Hash \(md5\):[ ]*([^\s]+)", output.decode("utf-8"))
        if not match:
            raise BuildkiteException("Couldn't parse md5 hash. gsutil output format changed?")
        expected_md5hash = base64.b64decode(match.group(1))

        output = subprocess.check_output(
            [gsutil_command(), "cat", bazelci_builds_metadata_url()], env=os.environ)
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
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
    return sha256.hexdigest()


def try_publish_binaries(build_number, expected_generation):
    now = datetime.datetime.now()
    git_commit = os.environ["BUILDKITE_COMMIT"]
    info = {
        "build_number": build_number,
        "build_time": now.strftime("%d-%m-%Y %H:%M"),
        "git_commit": git_commit,
        "platforms": {}
    }
    for platform in (name for name in PLATFORMS if PLATFORMS[name]["publish_binary"]):
        tmpdir = tempfile.mkdtemp()
        try:
            bazel_binary_path = download_bazel_binary(tmpdir, platform)
            execute_command([gsutil_command(), "cp", "-a", "public-read", bazel_binary_path,
                             bazelci_builds_gs_url(platform, git_commit)])
            info["platforms"][platform] = {
                "url": bazelci_builds_download_url(platform, git_commit),
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

# This is so that multiline python strings are represnted as YAML
# block strings
def str_presenter(dumper, data):
  if len(data.splitlines()) > 1:  # check for multiline string
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
  return dumper.represent_scalar('tag:yaml.org,2002:str', data)

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    yaml.add_representer(str, str_presenter)

    parser = argparse.ArgumentParser(description="Bazel Continuous Integration Script")

    subparsers = parser.add_subparsers(dest="subparsers_name")

    bazel_publish_binaries_pipeline = subparsers.add_parser("bazel_publish_binaries_pipeline")
    bazel_publish_binaries_pipeline.add_argument("--file_config", type=str)
    bazel_publish_binaries_pipeline.add_argument("--http_config", type=str)
    bazel_publish_binaries_pipeline.add_argument("--git_repository", type=str)

    bazel_downstream_pipeline = subparsers.add_parser("bazel_downstream_pipeline")
    bazel_downstream_pipeline.add_argument("--file_config", type=str)
    bazel_downstream_pipeline.add_argument("--http_config", type=str)
    bazel_downstream_pipeline.add_argument("--git_repository", type=str)
    bazel_downstream_pipeline.add_argument("--test_incompatible_flags", type=bool, nargs="?", const=True)
    bazel_downstream_pipeline.add_argument("--test_disabled_projects", type=bool, nargs="?", const=True)

    project_pipeline = subparsers.add_parser("project_pipeline")
    project_pipeline.add_argument("--project_name", type=str)
    project_pipeline.add_argument("--file_config", type=str)
    project_pipeline.add_argument("--http_config", type=str)
    project_pipeline.add_argument("--git_repository", type=str)
    project_pipeline.add_argument("--monitor_flaky_tests", type=bool, nargs="?", const=True)
    project_pipeline.add_argument("--use_but", type=bool, nargs="?", const=True)
    project_pipeline.add_argument("--incompatible_flag", type=str, action='append')

    runner = subparsers.add_parser("runner")
    runner.add_argument("--platform", action="store", choices=list(PLATFORMS))
    runner.add_argument("--file_config", type=str)
    runner.add_argument("--http_config", type=str)
    runner.add_argument("--git_repository", type=str)
    runner.add_argument("--git_commit", type=str, help="Reset the git repository to this commit after cloning it")
    runner.add_argument("--git_repo_location", type=str, help="Use an existing repository instead of cloning from github")
    runner.add_argument("--use_bazel_at_commit", type=str, help="Use Bazel binariy built at a specifc commit")
    runner.add_argument("--use_but", type=bool, nargs="?", const=True)
    runner.add_argument("--save_but", type=bool, nargs="?", const=True)
    runner.add_argument("--build_only", type=bool, nargs="?", const=True)
    runner.add_argument("--test_only", type=bool, nargs="?", const=True)
    runner.add_argument("--monitor_flaky_tests", type=bool, nargs="?", const=True)
    runner.add_argument("--incompatible_flag", type=str, action='append')

    runner = subparsers.add_parser("publish_binaries")

    runner = subparsers.add_parser("try_update_last_green_commit")

    args = parser.parse_args(argv)

    try:
        if args.subparsers_name == "bazel_publish_binaries_pipeline":
            configs = fetch_configs(args.http_config, args.file_config)
            print_bazel_publish_binaries_pipeline(configs=configs.get("platforms", None),
                                                  http_config=args.http_config,
                                                  file_config=args.file_config)
        elif args.subparsers_name == "bazel_downstream_pipeline":
            configs = fetch_configs(args.http_config, args.file_config)
            print_bazel_downstream_pipeline(configs=configs.get("platforms", None),
                                            http_config=args.http_config,
                                            file_config=args.file_config,
                                            test_incompatible_flags=args.test_incompatible_flags,
                                            test_disabled_projects=args.test_disabled_projects)
        elif args.subparsers_name == "project_pipeline":
            configs = fetch_configs(args.http_config, args.file_config)
            print_project_pipeline(platform_configs=configs.get("platforms", None),
                                   project_name=args.project_name,
                                   http_config=args.http_config,
                                   file_config=args.file_config,
                                   git_repository=args.git_repository,
                                   monitor_flaky_tests=args.monitor_flaky_tests,
                                   use_but=args.use_but,
                                   incompatible_flags=args.incompatible_flag)
        elif args.subparsers_name == "runner":
            configs = fetch_configs(args.http_config, args.file_config)
            execute_commands(config=configs.get("platforms", None)[args.platform],
                             platform=args.platform,
                             git_repository=args.git_repository,
                             git_commit=args.git_commit,
                             git_repo_location=args.git_repo_location,
                             use_bazel_at_commit=args.use_bazel_at_commit,
                             use_but=args.use_but,
                             save_but=args.save_but,
                             build_only=args.build_only,
                             test_only=args.test_only,
                             monitor_flaky_tests=args.monitor_flaky_tests,
                             incompatible_flags=args.incompatible_flag)
        elif args.subparsers_name == "publish_binaries":
            publish_binaries()
        elif args.subparsers_name == "try_update_last_green_commit":
            try_update_last_green_commit()
        else:
            parser.print_help()
            return 2
    except BuildkiteException as e:
        eprint(str(e))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
