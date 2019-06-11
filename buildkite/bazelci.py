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
from urllib.request import url2pathname
from urllib.parse import urlparse

# Initialize the random number generator.
random.seed()

BUILDKITE_ORG = os.environ["BUILDKITE_ORGANIZATION_SLUG"]
THIS_IS_PRODUCTION = BUILDKITE_ORG == "bazel-untrusted"
THIS_IS_TESTING = BUILDKITE_ORG == "bazel-testing"
THIS_IS_TRUSTED = BUILDKITE_ORG == "bazel-trusted"
THIS_IS_SPARTA = True

CLOUD_PROJECT = "bazel-public" if THIS_IS_TRUSTED else "bazel-untrusted"

GITHUB_BRANCH = {"bazel": "master", "bazel-trusted": "master", "bazel-testing": "testing"}[
    BUILDKITE_ORG
]

SCRIPT_URL = "https://raw.githubusercontent.com/bazelbuild/continuous-integration/{}/buildkite/bazelci.py?{}".format(
    GITHUB_BRANCH, int(time.time())
)

INCOMPATIBLE_FLAG_VERBOSE_FAILURES_URL = "https://raw.githubusercontent.com/bazelbuild/continuous-integration/{}/buildkite/incompatible_flag_verbose_failures.py?{}".format(
    GITHUB_BRANCH, int(time.time())
)

AGGREGATE_INCOMPATIBLE_TEST_RESULT_URL = "https://raw.githubusercontent.com/bazelbuild/continuous-integration/{}/buildkite/aggregate_incompatible_flags_test_result.py?{}".format(
    GITHUB_BRANCH, int(time.time())
)

EMERGENCY_FILE_URL = "https://raw.githubusercontent.com/bazelbuild/continuous-integration/{}/buildkite/emergency.yml?{}".format(
    GITHUB_BRANCH, int(time.time())
)

FLAKY_TESTS_BUCKET = {
    "bazel-testing": "gs://bazel-testing-buildkite-stats/flaky-tests-bep/",
    "bazel-trusted": "gs://bazel-buildkite-stats/flaky-tests-bep/",
    "bazel": "gs://bazel-buildkite-stats/flaky-tests-bep/",
}[BUILDKITE_ORG]

DOWNSTREAM_PROJECTS_PRODUCTION = {
    "Android Studio Plugin": {
        "git_repository": "https://github.com/bazelbuild/intellij.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/intellij/master/.bazelci/android-studio.yml",
        "pipeline_slug": "android-studio-plugin",
    },
    "Android Testing": {
        "git_repository": "https://github.com/googlesamples/android-testing.git",
        "http_config": "https://raw.githubusercontent.com/googlesamples/android-testing/master/bazelci/buildkite-pipeline.yml",
        "pipeline_slug": "android-testing",
    },
    "Bazel": {
        "git_repository": "https://github.com/bazelbuild/bazel.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/bazel/master/.bazelci/postsubmit.yml",
        "pipeline_slug": "bazel-bazel",
    },
    "Bazel Bench": {
        "git_repository": "https://github.com/bazelbuild/bazel-bench.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/bazel-bench/master/.bazelci/postsubmit.yml",
        "pipeline_slug": "bazel-bench",
    },
    "Bazel Codelabs": {
        "git_repository": "https://github.com/bazelbuild/codelabs.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/codelabs/master/.bazelci/presubmit.yml",
        "pipeline_slug": "bazel-codelabs",
    },
    "Bazel Remote Cache": {
        "git_repository": "https://github.com/buchgr/bazel-remote.git",
        "http_config": "https://raw.githubusercontent.com/buchgr/bazel-remote/master/.bazelci/presubmit.yml",
        "pipeline_slug": "bazel-remote-cache",
        "disabled_reason": "https://github.com/buchgr/bazel-remote/issues/82",
    },
    "Bazel integration testing": {
        "git_repository": "https://github.com/bazelbuild/bazel-integration-testing.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/bazel-integration-testing/master/.bazelci/presubmit.yml",
        "pipeline_slug": "bazel-integration-testing",
    },
    "Bazel skylib": {
        "git_repository": "https://github.com/bazelbuild/bazel-skylib.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/bazel-skylib/master/.bazelci/presubmit.yml",
        "pipeline_slug": "bazel-skylib",
    },
    "Bazel toolchains": {
        "git_repository": "https://github.com/bazelbuild/bazel-toolchains.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/bazel-toolchains/master/.bazelci/presubmit.yml",
        "pipeline_slug": "bazel-toolchains",
    },
    "Bazel watcher": {
        "git_repository": "https://github.com/bazelbuild/bazel-watcher.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/bazel-watcher/master/.bazelci/presubmit.yml",
        "pipeline_slug": "bazel-watcher",
    },
    "Bazelisk": {
        "git_repository": "https://github.com/bazelbuild/bazelisk.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/bazelisk/master/.bazelci/config.yml",
        "pipeline_slug": "bazelisk",
    },
    "Buildfarm": {
        "git_repository": "https://github.com/bazelbuild/bazel-buildfarm.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/bazel-buildfarm/master/.bazelci/presubmit.yml",
        "pipeline_slug": "buildfarm-male-farmer",
    },
    "Buildtools": {
        "git_repository": "https://github.com/bazelbuild/buildtools.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/buildtools/master/.bazelci/presubmit.yml",
        "pipeline_slug": "buildtools",
    },
    "CLion Plugin": {
        "git_repository": "https://github.com/bazelbuild/intellij.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/intellij/master/.bazelci/clion.yml",
        "pipeline_slug": "clion-plugin",
    },
    "Cartographer": {
        "git_repository": "https://github.com/googlecartographer/cartographer.git",
        "http_config": "https://raw.githubusercontent.com/googlecartographer/cartographer/master/.bazelci/presubmit.yml",
        "pipeline_slug": "cartographer",
    },
    "Cloud Robotics Core": {
        "git_repository": "https://github.com/googlecloudrobotics/core.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/cloud-robotics-postsubmit.yml",
        "pipeline_slug": "cloud-robotics-core",
    },
    "Envoy": {
        "git_repository": "https://github.com/envoyproxy/envoy.git",
        "http_config": "https://raw.githubusercontent.com/envoyproxy/envoy/master/.bazelci/presubmit.yml",
        "pipeline_slug": "envoy",
    },
    "Flogger": {
        "git_repository": "https://github.com/google/flogger.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/flogger.yml",
        "pipeline_slug": "flogger",
    },
    "Gerrit": {
        "git_repository": "https://gerrit.googlesource.com/gerrit.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/gerrit-postsubmit.yml",
        "pipeline_slug": "gerrit",
    },
    "Google Logging": {
        "git_repository": "https://github.com/google/glog.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/glog-postsubmit.yml",
        "pipeline_slug": "google-logging",
    },
    "IntelliJ Plugin": {
        "git_repository": "https://github.com/bazelbuild/intellij.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/intellij/master/.bazelci/intellij.yml",
        "pipeline_slug": "intellij-plugin",
    },
    "IntelliJ Plugin Aspect": {
        "git_repository": "https://github.com/bazelbuild/intellij.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/intellij/master/.bazelci/aspect.yml",
        "pipeline_slug": "intellij-plugin-aspect",
    },
    "Kythe": {
        "git_repository": "https://github.com/kythe/kythe.git",
        "http_config": "https://raw.githubusercontent.com/kythe/kythe/master/.bazelci/presubmit.yml",
        "pipeline_slug": "kythe",
    },
    "Protobuf": {
        "git_repository": "https://github.com/google/protobuf.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/protobuf-postsubmit.yml",
        "pipeline_slug": "protobuf",
    },
    "Skydoc": {
        "git_repository": "https://github.com/bazelbuild/skydoc.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/skydoc/master/.bazelci/presubmit.yml",
        "pipeline_slug": "skydoc",
    },
    "Subpar": {
        "git_repository": "https://github.com/google/subpar.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/subpar-postsubmit.yml",
        "pipeline_slug": "subpar",
    },
    "TensorFlow": {
        "git_repository": "https://github.com/tensorflow/tensorflow.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/tensorflow-postsubmit.yml",
        "pipeline_slug": "tensorflow",
        "disabled_reason": "Waiting for fix from protobuf: https://github.com/protocolbuffers/protobuf/pull/6207",
    },
    "Tulsi": {
        "git_repository": "https://github.com/bazelbuild/tulsi.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/tulsi/master/.bazelci/presubmit.yml",
        "pipeline_slug": "tulsi-bazel-darwin",
    },
    "re2": {
        "git_repository": "https://github.com/google/re2.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/re2-postsubmit.yml",
        "pipeline_slug": "re2",
    },
    "rules_android": {
        "git_repository": "https://github.com/bazelbuild/rules_android.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_android/master/.bazelci/postsubmit.yml",
        "pipeline_slug": "rules-android",
    },
    "rules_appengine": {
        "git_repository": "https://github.com/bazelbuild/rules_appengine.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_appengine/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-appengine-appengine",
    },
    "rules_apple": {
        "git_repository": "https://github.com/bazelbuild/rules_apple.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_apple/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-apple-darwin",
    },
    "rules_cc": {
        "git_repository": "https://github.com/bazelbuild/rules_cc.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_cc/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-cc",
    },
    "rules_closure": {
        "git_repository": "https://github.com/bazelbuild/rules_closure.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_closure/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-closure-closure-compiler",
    },
    "rules_d": {
        "git_repository": "https://github.com/bazelbuild/rules_d.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_d/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-d",
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
        "pipeline_slug": "rules-go-golang",
    },
    "rules_groovy": {
        "git_repository": "https://github.com/bazelbuild/rules_groovy.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_groovy/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-groovy",
    },
    "rules_gwt": {
        "git_repository": "https://github.com/bazelbuild/rules_gwt.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_gwt/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-gwt",
        "disabled_reason": "https://github.com/bazelbuild/rules_gwt/issues/23",
    },
    "rules_jsonnet": {
        "git_repository": "https://github.com/bazelbuild/rules_jsonnet.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_jsonnet/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-jsonnet",
    },
    "rules_jvm_external": {
        "git_repository": "https://github.com/bazelbuild/rules_jvm_external.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_jvm_external/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-jvm-external",
    },
    "rules_jvm_external - examples": {
        "git_repository": "https://github.com/bazelbuild/rules_jvm_external.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_jvm_external/master/.bazelci/examples.yml",
        "pipeline_slug": "rules-jvm-external-examples",
    },
    "rules_k8s": {
        "git_repository": "https://github.com/bazelbuild/rules_k8s.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_k8s/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-k8s-k8s",
    },
    "rules_kotlin": {
        "git_repository": "https://github.com/bazelbuild/rules_kotlin.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_kotlin/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-kotlin-kotlin",
    },
    "rules_nodejs": {
        "git_repository": "https://github.com/bazelbuild/rules_nodejs.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_nodejs/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-nodejs-nodejs",
    },
    "rules_perl": {
        "git_repository": "https://github.com/bazelbuild/rules_perl.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_perl/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-perl",
    },
    "rules_python": {
        "git_repository": "https://github.com/bazelbuild/rules_python.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_python/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-python-python",
    },
    "rules_rust": {
        "git_repository": "https://github.com/bazelbuild/rules_rust.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_rust/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-rust-rustlang",
    },
    "rules_sass": {
        "git_repository": "https://github.com/bazelbuild/rules_sass.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_sass/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-sass",
    },
    "rules_scala": {
        "git_repository": "https://github.com/bazelbuild/rules_scala.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_scala/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-scala-scala",
    },
    "rules_swift": {
        "git_repository": "https://github.com/bazelbuild/rules_swift.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_swift/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-swift-swift",
    },
    "rules_typescript": {
        "git_repository": "https://github.com/bazelbuild/rules_typescript.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_typescript/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-typescript-typescript",
    },
    "rules_webtesting": {
        "git_repository": "https://github.com/bazelbuild/rules_webtesting.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_webtesting/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-webtesting-saucelabs",
    },
    "upb": {
        "git_repository": "https://github.com/protocolbuffers/upb.git",
        "http_config": "https://raw.githubusercontent.com/protocolbuffers/upb/master/.bazelci/presubmit.yml",
        "pipeline_slug": "upb",
        "disabled_reason": "https://github.com/protocolbuffers/upb/issues/172",
    },
}

DOWNSTREAM_PROJECTS_TESTING = {
    "Bazel": DOWNSTREAM_PROJECTS_PRODUCTION["Bazel"],
    "Bazelisk": DOWNSTREAM_PROJECTS_PRODUCTION["Bazelisk"],
    "Federation": {
        "git_repository": "https://github.com/fweikert/bazel-federation.git",
        "http_config": "https://raw.githubusercontent.com/fweikert/bazel-federation/master/.bazelci/presubmit.yml",
        "pipeline_slug": "bazel-federation",
    },
    "rules_docker": DOWNSTREAM_PROJECTS_PRODUCTION["rules_docker"],
    "rules_go": DOWNSTREAM_PROJECTS_PRODUCTION["rules_go"],
    "rules_groovy": DOWNSTREAM_PROJECTS_PRODUCTION["rules_groovy"],
    "rules_kotlin": DOWNSTREAM_PROJECTS_PRODUCTION["rules_kotlin"],
    "rules_nodejs": DOWNSTREAM_PROJECTS_PRODUCTION["rules_nodejs"],
    "rules_rust": DOWNSTREAM_PROJECTS_PRODUCTION["rules_rust"],
    "rules_scala": DOWNSTREAM_PROJECTS_PRODUCTION["rules_scala"],
}

DOWNSTREAM_PROJECTS = {
    "bazel-testing": DOWNSTREAM_PROJECTS_TESTING,
    "bazel-trusted": {},
    "bazel": DOWNSTREAM_PROJECTS_PRODUCTION,
}[BUILDKITE_ORG]

# A map containing all supported platform names as keys, with the values being
# the platform name in a human readable format, and a the buildkite-agent's
# working directory.
PLATFORMS = {
    "ubuntu1604": {
        "name": "Ubuntu 16.04, OpenJDK 8",
        "emoji-name": ":ubuntu: 16.04 (OpenJDK 8)",
        "downstream-root": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": ["ubuntu1404", "ubuntu1604", "linux"],
        "docker-image": "gcr.io/bazel-public/ubuntu1604:java8",
        "python": "python3.6",
    },
    "ubuntu1804": {
        "name": "Ubuntu 18.04, OpenJDK 11",
        "emoji-name": ":ubuntu: 18.04 (OpenJDK 11)",
        "downstream-root": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": ["ubuntu1804"],
        "docker-image": "gcr.io/bazel-public/ubuntu1804:java11",
        "python": "python3.6",
    },
    "ubuntu1804_nojava": {
        "name": "Ubuntu 18.04, no JDK",
        "emoji-name": ":ubuntu: 18.04 (no JDK)",
        "downstream-root": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": [],
        "docker-image": "gcr.io/bazel-public/ubuntu1804:nojava",
        "python": "python3.6",
    },
    "macos": {
        "name": "macOS, OpenJDK 8",
        "emoji-name": ":darwin: (OpenJDK 8)",
        "downstream-root": "/Users/buildkite/builds/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": ["macos"],
        "queue": "macos",
        "python": "python3.7",
    },
    "windows": {
        "name": "Windows, OpenJDK 8",
        "emoji-name": ":windows: (OpenJDK 8)",
        "downstream-root": "d:/b/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": ["windows"],
        "queue": "windows",
        "python": "python.exe",
    },
    "rbe_ubuntu1604": {
        "name": "RBE (Ubuntu 16.04, OpenJDK 8)",
        "emoji-name": ":gcloud: (OpenJDK 8)",
        "downstream-root": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": [],
        "docker-image": "gcr.io/bazel-public/ubuntu1604:java8",
        "python": "python3.6",
    },
}

BUILDIFIER_DOCKER_IMAGE = "gcr.io/bazel-public/buildifier"

# The platform used for various steps (e.g. stuff that formerly ran on the "pipeline" workers).
DEFAULT_PLATFORM = "ubuntu1804"

DEFAULT_XCODE_VERSION = "10.2.1"
XCODE_VERSION_REGEX = re.compile(r"^\d+\.\d+(\.\d+)?$")

ENCRYPTED_SAUCELABS_TOKEN = """
CiQAry63sOlZtTNtuOT5DAOLkum0rGof+DOweppZY1aOWbat8zwSTQAL7Hu+rgHSOr6P4S1cu4YG
/I1BHsWaOANqUgFt6ip9/CUGGJ1qggsPGXPrmhSbSPqNAIAkpxYzabQ3mfSIObxeBmhKg2dlILA/
EDql
""".strip()

BUILD_LABEL_PATTERN = re.compile(r"^Build label: (\S+)$", re.MULTILINE)

BUILDIFIER_VERSION_ENV_VAR = "BUILDIFIER_VERSION"

BUILDIFIER_WARNINGS_ENV_VAR = "BUILDIFIER_WARNINGS"

BUILDIFIER_STEP_NAME = "Buildifier"

SKIP_TASKS_ENV_VAR = "CI_SKIP_TASKS"

CONFIG_FILE_EXTENSIONS = set([".yml", ".yaml"])


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


class BuildkiteClient(object):

    _ENCRYPTED_BUILDKITE_API_TOKEN = """
CiQA4DEB9ldzC+E39KomywtqXfaQ86hhulgeDsicds2BuvbCYzsSUAAqwcvXZPh9IMWlwWh94J2F
exosKKaWB0tSRJiPKnv2NPDfEqGul0ZwVjtWeASpugwxxKeLhFhPMcgHMPfndH6j2GEIY6nkKRbP
uwoRMCwe
""".strip()

    _ENCRYPTED_BUILDKITE_API_TESTING_TOKEN = """
CiQAMTBkWjL1C+F5oon3+cC1vmum5+c1y5+96WQY44p0Lxd0PeASUQAy7iU0c6E3W5EOSFYfD5fA
MWy/SHaMno1NQSUa4xDOl5yc2kizrtxPPVkX4x9pLNuGUY/xwAn2n1DdiUdWZNWlY1bX2C4ex65e
P9w8kNhEbw==
""".strip()

    _BUILD_STATUS_URL_TEMPLATE = (
        "https://api.buildkite.com/v2/organizations/{}/pipelines/{}/builds/{}"
    )

    def __init__(self, org, pipeline):
        self._org = org
        self._pipeline = pipeline
        self._token = self._get_buildkite_token()

    def _get_buildkite_token(self):
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
                    "buildkite-testing-api-token"
                    if THIS_IS_TESTING
                    else "buildkite-untrusted-api-token",
                    "--ciphertext-file",
                    "-",
                    "--plaintext-file",
                    "-",
                ],
                input=base64.b64decode(
                    self._ENCRYPTED_BUILDKITE_API_TESTING_TOKEN
                    if THIS_IS_TESTING
                    else self._ENCRYPTED_BUILDKITE_API_TOKEN
                ),
                env=os.environ,
            )
            .decode("utf-8")
            .strip()
        )

    def _open_url(self, url):
        return (
            urllib.request.urlopen("{}?access_token={}".format(url, self._token))
            .read()
            .decode("utf-8")
        )

    def get_build_info(self, build_number):
        url = self._BUILD_STATUS_URL_TEMPLATE.format(self._org, self._pipeline, build_number)
        output = self._open_url(url)
        return json.loads(output)

    def get_build_log(self, job):
        return self._open_url(job["raw_log_url"])


def eprint(*args, **kwargs):
    """
    Print to stderr and flush (just in case).
    """
    print(*args, flush=True, file=sys.stderr, **kwargs)


def is_windows():
    return os.name == "nt"


def gsutil_command():
    return "gsutil.cmd" if is_windows() else "gsutil"


def gcloud_command():
    return "gcloud.cmd" if is_windows() else "gcloud"


def downstream_projects_root(platform):
    downstream_root = os.path.expandvars(PLATFORMS[platform]["downstream-root"])
    if not os.path.exists(downstream_root):
        os.makedirs(downstream_root)
    return downstream_root


def fetch_configs(http_url, file_config):
    """
    If specified fetches the build configuration from file_config or http_url, else tries to
    read it from .bazelci/presubmit.yml.
    Returns the json configuration as a python data structure.
    """
    if file_config is not None and http_url is not None:
        raise BuildkiteException("file_config and http_url cannot be set at the same time")

    config = load_config(http_url, file_config)
    # Legacy mode means that there is exactly one task per platform (e.g. ubuntu1604_nojdk),
    # which means that we can get away with using the platform name as task ID.
    # No other updates are needed since get_platform_for_task() falls back to using the
    # task ID as platform if there is no explicit "platforms" field.
    if "platforms" in config:
        config["tasks"] = config.pop("platforms")

    return config


def load_config(http_url, file_config):
    if file_config is not None:
        with open(file_config, "r") as fd:
            return yaml.safe_load(fd)
    if http_url is not None:
        return load_remote_yaml_file(http_url)
    with open(".bazelci/presubmit.yml", "r") as fd:
        return yaml.safe_load(fd)


def load_remote_yaml_file(http_url):
    with urllib.request.urlopen(http_url) as resp:
        reader = codecs.getreader("utf-8")
        return yaml.safe_load(reader(resp))


def print_collapsed_group(name):
    eprint("\n\n--- {0}\n\n".format(name))


def print_expanded_group(name):
    eprint("\n\n+++ {0}\n\n".format(name))


def use_bazelisk_migrate():
    """
    If USE_BAZELISK_MIGRATE is set, we use `bazelisk --migrate` to test incompatible flags.
    """
    return bool(os.environ.get("USE_BAZELISK_MIGRATE"))


def bazelisk_flags():
    return ["--migrate"] if use_bazelisk_migrate() else []


def execute_commands(
    task_config,
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
    bazel_version=None,
):
    # If we want to test incompatible flags, we ignore bazel_version and always use
    # the latest Bazel version through Bazelisk.
    if incompatible_flags:
        bazel_version = None
    if not bazel_version:
        # The last good version of Bazel can be specified in an emergency file.
        # However, we only use last_good_bazel for pipelines that do not
        # explicitly specify a version of Bazel.
        try:
            emergency_settings = load_remote_yaml_file(EMERGENCY_FILE_URL)
            bazel_version = emergency_settings.get("last_good_bazel")
        except urllib.error.HTTPError:
            # Ignore this error. The Setup step will have already complained about
            # it by showing an error message.
            pass

    if build_only and test_only:
        raise BuildkiteException("build_only and test_only cannot be true at the same time")

    if use_bazel_at_commit and use_but:
        raise BuildkiteException("use_bazel_at_commit cannot be set when use_but is true")

    tmpdir = tempfile.mkdtemp()
    sc_process = None
    try:
        if platform == "macos":
            activate_xcode(task_config)

        # If the CI worker runs Bazelisk, we need to forward all required env variables to the test.
        # Otherwise any integration test that invokes Bazel (=Bazelisk in this case) will fail.
        test_env_vars = ["LocalAppData"] if platform == "windows" else ["HOME"]
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
            if bazel_version:
                # This will only work if the bazel binary in $PATH is actually a bazelisk binary
                # (https://github.com/bazelbuild/bazelisk).
                os.environ["USE_BAZEL_VERSION"] = bazel_version
                test_env_vars.append("USE_BAZEL_VERSION")

        for key, value in task_config.get("environment", {}).items():
            # We have to explicitly convert the value to a string, because sometimes YAML tries to
            # be smart and converts strings like "true" and "false" to booleans.
            os.environ[key] = str(value)

        # Allow the config to override the current working directory.
        required_prefix = os.getcwd()
        requested_working_dir = os.path.abspath(task_config.get("working_directory", ""))
        if os.path.commonpath([required_prefix, requested_working_dir]) != required_prefix:
            raise BuildkiteException("working_directory refers to a path outside the workspace")
        os.chdir(requested_working_dir)

        if platform == "windows":
            execute_batch_commands(task_config.get("batch_commands", None))
        else:
            execute_shell_commands(task_config.get("shell_commands", None))

        bazel_version = print_bazel_version_info(bazel_binary, platform)

        print_environment_variables_info()

        if incompatible_flags:
            print_expanded_group("Build and test with the following incompatible flags:")
            for flag in incompatible_flags:
                eprint(flag + "\n")

        execute_bazel_run(
            bazel_binary, platform, task_config.get("run_targets", None), incompatible_flags
        )

        if task_config.get("sauce"):
            sc_process = start_sauce_connect_proxy(platform, tmpdir)

        if needs_clean:
            execute_bazel_clean(bazel_binary, platform)

        build_targets, test_targets = calculate_targets(
            task_config, platform, bazel_binary, build_only, test_only
        )

        include_json_profile = task_config.get("include_json_profile", [])

        if build_targets:
            json_profile_flags = []
            include_json_profile_build = "build" in include_json_profile
            if include_json_profile_build:
                json_profile_out_build = os.path.join(tmpdir, "build.profile.gz")
                json_profile_flags = get_json_profile_flags(json_profile_out_build)

            build_flags = task_config.get("build_flags") or []
            try:
                execute_bazel_build(
                    bazel_version,
                    bazel_binary,
                    platform,
                    build_flags + json_profile_flags,
                    build_targets,
                    None,
                    incompatible_flags,
                )
                if save_but:
                    upload_bazel_binary(platform)
            finally:
                if include_json_profile_build:
                    upload_json_profile(json_profile_out_build, tmpdir)

        if test_targets:
            json_profile_flags = []
            include_json_profile_test = "test" in include_json_profile
            if include_json_profile_test:
                json_profile_out_test = os.path.join(tmpdir, "test.profile.gz")
                json_profile_flags = get_json_profile_flags(json_profile_out_test)

            test_flags = task_config.get("test_flags") or []
            test_flags += json_profile_flags
            if test_env_vars:
                test_flags += ["--test_env={}".format(v) for v in test_env_vars]

            if not is_windows():
                # On platforms that support sandboxing (Linux, MacOS) we have
                # to allow access to Bazelisk's cache directory.
                # However, the flag requires the directory to exist,
                # so we create it here in order to not crash when a test
                # does not invoke Bazelisk.
                bazelisk_cache_dir = get_bazelisk_cache_directory(platform)
                os.makedirs(bazelisk_cache_dir, mode=0o755, exist_ok=True)
                test_flags.append("--sandbox_writable_path={}".format(bazelisk_cache_dir))

            test_bep_file = os.path.join(tmpdir, "test_bep.json")
            try:
                execute_bazel_test(
                    bazel_version,
                    bazel_binary,
                    platform,
                    test_flags,
                    test_targets,
                    test_bep_file,
                    monitor_flaky_tests,
                    incompatible_flags,
                )
                if monitor_flaky_tests:
                    upload_bep_logs_for_flaky_tests(test_bep_file)
            finally:
                upload_test_logs(test_bep_file, tmpdir)
                if include_json_profile_test:
                    upload_json_profile(json_profile_out_test, tmpdir)
    finally:
        if sc_process:
            sc_process.terminate()
            try:
                sc_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                sc_process.kill()
        if tmpdir:
            shutil.rmtree(tmpdir)


def activate_xcode(task_config):
    # Get the Xcode version from the config.
    xcode_version = task_config.get("xcode_version", DEFAULT_XCODE_VERSION)
    print_collapsed_group("Activating Xcode {}...".format(xcode_version))

    # Ensure it's a valid version number.
    if not isinstance(xcode_version, str):
        raise BuildkiteException(
            "Version number '{}' is not a string. Did you forget to put it in quotes?".format(
                xcode_version
            )
        )
    if not XCODE_VERSION_REGEX.match(xcode_version):
        raise BuildkiteException(
            "Invalid Xcode version format '{}', must match the format X.Y[.Z].".format(
                xcode_version
            )
        )

    # Check that the selected Xcode version is actually installed on the host.
    xcode_path = "/Applications/Xcode{}.app".format(xcode_version)
    if not os.path.exists(xcode_path):
        raise BuildkiteException("Xcode not found at '{}'.".format(xcode_path))

    # Now activate the specified Xcode version and let it install its required components.
    # The CI machines have a sudoers config that allows the 'buildkite' user to run exactly
    # these two commands, so don't change them without also modifying the file there.
    execute_command(["/usr/bin/sudo", "/usr/bin/xcode-select", "--switch", xcode_path])
    execute_command(["/usr/bin/sudo", "/usr/bin/xcodebuild", "-runFirstLaunch"])


def get_bazelisk_cache_directory(platform):
    # The path relies on the behavior of Go's os.UserCacheDir()
    # and of the Go version of Bazelisk.
    dir = "Library/Caches" if platform == "macos" else ".cache"
    return os.path.join(os.environ.get("HOME"), dir, "bazelisk")


def tests_with_status(bep_file, status):
    return set(label for label, _ in test_logs_for_status(bep_file, status=status))


def start_sauce_connect_proxy(platform, tmpdir):
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
            raise BuildkiteException(
                "Sauce Connect Proxy is still not ready after 30 seconds, aborting!"
            )
        time.sleep(1)
    print("Sauce Connect Proxy is ready, continuing...")
    return sc_process


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


def is_pull_request():
    third_party_repo = os.getenv("BUILDKITE_PULL_REQUEST_REPO", "")
    return len(third_party_repo) > 0


def has_flaky_tests(bep_file):
    return len(test_logs_for_status(bep_file, status="FLAKY")) > 0


def print_bazel_version_info(bazel_binary, platform):
    print_collapsed_group(":information_source: Bazel Info")
    version_output = execute_command_and_get_output(
        [bazel_binary]
        + common_startup_flags(platform)
        + ["--nomaster_bazelrc", "--bazelrc=/dev/null", "version"]
    )
    execute_command(
        [bazel_binary]
        + common_startup_flags(platform)
        + ["--nomaster_bazelrc", "--bazelrc=/dev/null", "info"]
    )

    match = BUILD_LABEL_PATTERN.search(version_output)
    return match.group(1) if match else "unreleased binary"


def print_environment_variables_info():
    print_collapsed_group(":information_source: Environment Variables")
    for key, value in os.environ.items():
        eprint("%s=(%s)" % (key, value))


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
    execute_command(
        ["buildkite-agent", "artifact", "download", binary_path, dest_dir, "--step", source_step]
    )
    bazel_binary_path = os.path.join(dest_dir, binary_path)
    st = os.stat(bazel_binary_path)
    os.chmod(bazel_binary_path, st.st_mode | stat.S_IEXEC)
    return bazel_binary_path


def download_bazel_binary_at_commit(dest_dir, platform, bazel_git_commit):
    # We have a few Ubuntu platforms for which we don't build binaries. It should be OK to use the
    # ones from Ubuntu 16.04 on them.
    if "ubuntu" in platform and not should_publish_binaries_for_platform(platform):
        platform = "ubuntu1604"
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
        raise BuildkiteException(
            "Failed to download Bazel binary at %s, error message:\n%s" % (bazel_git_commit, str(e))
        )
    st = os.stat(bazel_binary_path)
    os.chmod(bazel_binary_path, st.st_mode | stat.S_IEXEC)
    return bazel_binary_path


def get_mirror_path(git_repository, platform):
    mirror_root = {
        "macos": "/usr/local/var/bazelbuild/",
        "windows": "c:\\buildkite\\bazelbuild\\",
    }.get(platform, "/var/lib/bazelbuild/")

    return mirror_root + re.sub(r"[^0-9A-Za-z]", "-", git_repository)


def clone_git_repository(git_repository, platform, git_commit=None):
    root = downstream_projects_root(platform)
    project_name = re.search(r"/([^/]+)\.git$", git_repository).group(1)
    clone_path = os.path.join(root, project_name)
    print_collapsed_group(
        "Fetching %s sources at %s" % (project_name, git_commit if git_commit else "HEAD")
    )

    mirror_path = get_mirror_path(git_repository, platform)

    if not os.path.exists(clone_path):
        if os.path.exists(mirror_path):
            execute_command(
                ["git", "clone", "-v", "--reference", mirror_path, git_repository, clone_path]
            )
        else:
            execute_command(["git", "clone", "-v", git_repository, clone_path])

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


def handle_bazel_failure(exception, action):
    msg = "bazel {0} failed with exit code {1}".format(action, exception.returncode)
    if use_bazelisk_migrate():
        print_collapsed_group(msg)
    else:
        raise BuildkiteException(msg)


def execute_bazel_run(bazel_binary, platform, targets, incompatible_flags):
    if not targets:
        return
    print_collapsed_group("Setup (Run Targets)")
    # When using bazelisk --migrate to test incompatible flags,
    # incompatible flags set by "INCOMPATIBLE_FLAGS" env var will be ignored.
    incompatible_flags_to_use = (
        [] if (use_bazelisk_migrate() or not incompatible_flags) else incompatible_flags
    )
    for target in targets:
        try:
            execute_command(
                [bazel_binary]
                + bazelisk_flags()
                + common_startup_flags(platform)
                + ["run"]
                + common_build_flags(None, platform)
                + incompatible_flags_to_use
                + [target]
            )
        except subprocess.CalledProcessError as e:
            handle_bazel_failure(e, "run")


def remote_caching_flags(platform):
    # Only enable caching for untrusted and testing builds.
    if CLOUD_PROJECT not in ["bazel-untrusted"]:
        return []

    platform_cache_key = [BUILDKITE_ORG.encode("utf-8")]

    if platform == "macos":
        platform_cache_key += [
            # macOS version:
            subprocess.check_output(["/usr/bin/sw_vers", "-productVersion"]),
            # Path to Xcode:
            subprocess.check_output(["/usr/bin/xcode-select", "-p"]),
            # Xcode version:
            subprocess.check_output(["/usr/bin/xcodebuild", "-version"]),
        ]
        # Use a local cache server for our macOS machines.
        flags = ["--remote_cache=http://100.107.73.186"]
    else:
        platform_cache_key += [
            # Platform name:
            platform.encode("utf-8")
        ]
        # Use RBE for caching builds running on GCE.
        flags = [
            "--google_default_credentials",
            "--remote_cache=remotebuildexecution.googleapis.com",
            "--remote_instance_name=projects/{}/instances/default_instance".format(CLOUD_PROJECT),
            "--tls_enabled=true",
        ]

    platform_cache_digest = hashlib.sha256()
    for key in platform_cache_key:
        eprint("Adding to platform cache key: {}".format(key))
        platform_cache_digest.update(key)
        platform_cache_digest.update(b":")

    flags += [
        "--remote_timeout=60",
        "--remote_max_connections=200",
        '--remote_default_platform_properties=properties:{name:"cache-silo-key" value:"%s"}'
        % platform_cache_digest.hexdigest(),
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
    return ["--output_user_root=D:/b"] if platform == "windows" else []


def common_build_flags(bep_file, platform):
    flags = [
        "--show_progress_rate_limit=5",
        "--curses=yes",
        "--color=yes",
        "--terminal_columns=143",
        "--show_timestamps",
        "--verbose_failures",
        "--keep_going",
        "--jobs=" + concurrent_jobs(platform),
        "--announce_rc",
        "--experimental_multi_threaded_digest",
        "--experimental_repository_cache_hardlinks",
        # Some projects set --disk_cache in their project-specific bazelrc, which we never want on
        # CI, so let's just disable it explicitly.
        "--disk_cache=",
    ]

    if platform == "windows":
        pass
    elif platform == "macos":
        flags += [
            "--sandbox_writable_path=/var/tmp/_bazel_buildkite/cache/repos/v1",
            "--test_env=REPOSITORY_CACHE=/var/tmp/_bazel_buildkite/cache/repos/v1",
        ]
    else:
        flags += ["--sandbox_tmpfs_path=/tmp"]

    if bep_file:
        flags += [
            "--experimental_build_event_json_file_path_conversion=false",
            "--build_event_json_file=" + bep_file,
        ]

    return flags


def rbe_flags(original_flags, accept_cached):
    # Enable remote execution via RBE.
    flags = [
        "--remote_executor=remotebuildexecution.googleapis.com",
        "--remote_instance_name=projects/bazel-untrusted/instances/default_instance",
        "--remote_timeout=3600",
        # TODO(pcloudy): Remove this flag after upgrading Bazel to 0.27.0
        "--incompatible_list_based_execution_strategy_selection",
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

    # Adapted from https://github.com/bazelbuild/bazel-toolchains/blob/master/bazelrc/.bazelrc
    flags += [
        # These should NOT longer need to be modified.
        # All that is needed is updating the @bazel_toolchains repo pin
        # in projects' WORKSPACE files.
        #
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
    # If you are using your own toolchain container, you need to create a platform
    # target with "constraint_values" that allow for the toolchain specified with
    # "extra_toolchains" to be selected (given constraints defined in
    # "exec_compatible_with").
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


def execute_bazel_clean(bazel_binary, platform):
    print_expanded_group(":bazel: Clean")

    try:
        execute_command([bazel_binary] + common_startup_flags(platform) + ["clean", "--expunge"])
    except subprocess.CalledProcessError as e:
        raise BuildkiteException("bazel clean failed with exit code {}".format(e.returncode))


def execute_bazel_build(
    bazel_version, bazel_binary, platform, flags, targets, bep_file, incompatible_flags
):
    print_collapsed_group(":bazel: Computing flags for build step")
    aggregated_flags = compute_flags(
        platform,
        flags,
        # When using bazelisk --migrate to test incompatible flags,
        # incompatible flags set by "INCOMPATIBLE_FLAGS" env var will be ignored.
        [] if (use_bazelisk_migrate() or not incompatible_flags) else incompatible_flags,
        bep_file,
        enable_remote_cache=True,
    )

    print_expanded_group(":bazel: Build ({})".format(bazel_version))
    try:
        execute_command(
            [bazel_binary]
            + bazelisk_flags()
            + common_startup_flags(platform)
            + ["build"]
            + aggregated_flags
            + targets
        )
    except subprocess.CalledProcessError as e:
        handle_bazel_failure(e, "build")


def calculate_targets(task_config, platform, bazel_binary, build_only, test_only):
    build_targets = [] if test_only else task_config.get("build_targets", [])
    test_targets = [] if build_only else task_config.get("test_targets", [])

    shard_id = int(os.getenv("BUILDKITE_PARALLEL_JOB", "-1"))
    shard_count = int(os.getenv("BUILDKITE_PARALLEL_JOB_COUNT", "-1"))
    if shard_id > -1 and shard_count > -1:
        print_collapsed_group(
            ":female-detective: Calculating targets for shard {}/{}".format(
                shard_id + 1, shard_count
            )
        )
        expanded_test_targets = expand_test_target_patterns(bazel_binary, platform, test_targets)
        build_targets, test_targets = get_targets_for_shard(
            build_targets, expanded_test_targets, shard_id, shard_count
        )

    return build_targets, test_targets


def expand_test_target_patterns(bazel_binary, platform, test_targets):
    included_targets, excluded_targets = partition_test_targets(test_targets)
    excluded_string = (
        " except tests(set({}))".format(" ".join("'{}'".format(t) for t in excluded_targets))
        if excluded_targets
        else ""
    )

    eprint("Resolving test targets via bazel query")
    output = execute_command_and_get_output(
        [bazel_binary]
        + common_startup_flags(platform)
        + [
            "--nomaster_bazelrc",
            "--bazelrc=/dev/null",
            "query",
            "tests(set({})){}".format(
                " ".join("'{}'".format(t) for t in included_targets), excluded_string
            ),
        ],
        print_output=False,
    )
    return output.split("\n")


def partition_test_targets(test_targets):
    included_targets, excluded_targets = [], []
    for target in test_targets:
        if target == "--":
            continue
        elif target.startswith("-"):
            excluded_targets.append(target[1:])
        else:
            included_targets.append(target)

    return included_targets, excluded_targets


def get_targets_for_shard(build_targets, test_targets, shard_id, shard_count):
    # TODO(fweikert): implement a more sophisticated algorithm
    build_targets_for_this_shard = sorted(build_targets)[shard_id::shard_count]
    test_targets_for_this_shard = sorted(test_targets)[shard_id::shard_count]

    return build_targets_for_this_shard, test_targets_for_this_shard


def execute_bazel_test(
    bazel_version,
    bazel_binary,
    platform,
    flags,
    targets,
    bep_file,
    monitor_flaky_tests,
    incompatible_flags,
):
    aggregated_flags = [
        "--flaky_test_attempts=3",
        "--build_tests_only",
        "--local_test_jobs=" + concurrent_test_jobs(platform),
    ]
    # Don't enable remote caching if the user enabled remote execution / caching themselves
    # or flaky test monitoring is enabled, as remote caching makes tests look less flaky than
    # they are.
    print_collapsed_group(":bazel: Computing flags for test step")
    aggregated_flags += compute_flags(
        platform,
        flags,
        # When using bazelisk --migrate to test incompatible flags,
        # incompatible flags set by "INCOMPATIBLE_FLAGS" env var will be ignored.
        [] if (use_bazelisk_migrate() or not incompatible_flags) else incompatible_flags,
        bep_file,
        enable_remote_cache=not monitor_flaky_tests,
    )

    print_expanded_group(":bazel: Test ({})".format(bazel_version))
    try:
        execute_command(
            [bazel_binary]
            + bazelisk_flags()
            + common_startup_flags(platform)
            + ["test"]
            + aggregated_flags
            + targets
        )
    except subprocess.CalledProcessError as e:
        handle_bazel_failure(e, "test")


def get_json_profile_flags(out_file):
    return [
        "--experimental_generate_json_trace_profile",
        "--experimental_profile_cpu_usage",
        "--experimental_json_trace_compression",
        "--profile={}".format(out_file),
    ]


def upload_bep_logs_for_flaky_tests(test_bep_file):
    if has_flaky_tests(test_bep_file):
        build_number = os.getenv("BUILDKITE_BUILD_NUMBER")
        pipeline_slug = os.getenv("BUILDKITE_PIPELINE_SLUG")
        execute_command(
            [
                gsutil_command(),
                "cp",
                test_bep_file,
                FLAKY_TESTS_BUCKET + pipeline_slug + "/" + build_number + ".json",
            ]
        )


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


def upload_json_profile(json_profile_path, tmpdir):
    if not os.path.exists(json_profile_path):
        return
    print_collapsed_group(":gcloud: Uploading JSON Profile")
    execute_command(["buildkite-agent", "artifact", "upload", json_profile_path], cwd=tmpdir)


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
                    test_logs.append(url2pathname(urlparse(output["uri"]).path))
                targets.append((test_target, test_logs))
        pos += size + 1
    return targets


def execute_command_and_get_output(args, shell=False, fail_if_nonzero=True, print_output=True):
    eprint(" ".join(args))
    process = subprocess.run(
        args,
        shell=shell,
        check=fail_if_nonzero,
        env=os.environ,
        stdout=subprocess.PIPE,
        errors="replace",
        universal_newlines=True,
    )
    if print_output:
        eprint(process.stdout)

    return process.stdout


def execute_command(args, shell=False, fail_if_nonzero=True, cwd=None):
    eprint(" ".join(args))
    return subprocess.run(
        args, shell=shell, check=fail_if_nonzero, env=os.environ, cwd=cwd
    ).returncode


def execute_command_background(args):
    eprint(" ".join(args))
    return subprocess.Popen(args, env=os.environ)


def create_step(label, commands, platform, shards=1):
    if "docker-image" in PLATFORMS[platform]:
        step = create_docker_step(
            label, image=PLATFORMS[platform]["docker-image"], commands=commands
        )
    else:
        step = {
            "label": label,
            "command": commands,
            "agents": {"queue": PLATFORMS[platform]["queue"]},
        }

    if shards > 1:
        step["label"] += " (shard %n)"
        step["parallelism"] = shards

    # Enforce a global 8 hour job timeout.
    step["timeout_in_minutes"] = 8 * 60

    # Automatically retry when an agent got lost (usually due to an infra flake).
    step["retry"] = {}
    step["retry"]["automatic"] = [{"exit_status": -1, "limit": 3}, {"exit_status": 137, "limit": 3}]

    return step


def create_docker_step(label, image, commands=None, additional_env_vars=None):
    env = ["ANDROID_HOME", "ANDROID_NDK_HOME", "BUILDKITE_ARTIFACT_UPLOAD_DESTINATION"]
    if additional_env_vars:
        env += ["{}={}".format(k, v) for k, v in additional_env_vars.items()]

    step = {
        "label": label,
        "command": commands,
        "agents": {"queue": "default"},
        "plugins": {
            "docker#v3.2.0": {
                "always-pull": True,
                "environment": env,
                "image": image,
                "network": "host",
                "privileged": True,
                "propagate-environment": True,
                "propagate-uid-gid": True,
                "volumes": [
                    "/etc/group:/etc/group:ro",
                    "/etc/passwd:/etc/passwd:ro",
                    "/opt:/opt:ro",
                    "/var/lib/buildkite-agent:/var/lib/buildkite-agent",
                    "/var/lib/gitmirrors:/var/lib/gitmirrors:ro",
                    "/var/run/docker.sock:/var/run/docker.sock",
                ],
            }
        },
    }
    if not step["command"]:
        del step["command"]
    return step


def print_project_pipeline(
    configs,
    project_name,
    http_config,
    file_config,
    git_repository,
    monitor_flaky_tests,
    use_but,
    incompatible_flags,
):
    task_configs = configs.get("tasks", None)
    if not task_configs:
        raise BuildkiteException("{0} pipeline configuration is empty.".format(project_name))

    pipeline_steps = []
    task_configs = filter_tasks_that_should_be_skipped(task_configs, pipeline_steps)

    # In Bazel Downstream Project pipelines, git_repository and project_name must be specified.
    is_downstream_project = (use_but or incompatible_flags) and git_repository and project_name

    buildifier_config = configs.get("buildifier")
    # Skip Buildifier when we test downstream projects.
    if buildifier_config and not is_downstream_project:
        buildifier_env_vars = {}
        if isinstance(buildifier_config, str):
            # Simple format:
            # ---
            # buildifier: latest
            buildifier_env_vars[BUILDIFIER_VERSION_ENV_VAR] = buildifier_config
        else:
            # Advanced format:
            # ---
            # buildifier:
            #   version: latest
            #   warnings: all

            def SetEnvVar(config_key, env_var_name):
                if config_key in buildifier_config:
                    buildifier_env_vars[env_var_name] = buildifier_config[config_key]

            SetEnvVar("version", BUILDIFIER_VERSION_ENV_VAR)
            SetEnvVar("warnings", BUILDIFIER_WARNINGS_ENV_VAR)

        if not buildifier_env_vars:
            raise BuildkiteException(
                'Invalid buildifier configuration entry "{}"'.format(buildifier_config)
            )

        pipeline_steps.append(
            create_docker_step(
                BUILDIFIER_STEP_NAME,
                image=BUILDIFIER_DOCKER_IMAGE,
                additional_env_vars=buildifier_env_vars,
            )
        )

    # In Bazel Downstream Project pipelines, we should test the project at the last green commit.
    git_commit = None
    if is_downstream_project:
        last_green_commit_url = bazelci_last_green_commit_url(
            git_repository, DOWNSTREAM_PROJECTS[project_name]["pipeline_slug"]
        )
        git_commit = get_last_green_commit(last_green_commit_url)

    config_hashes = set()
    for task, task_config in task_configs.items():
        # We override the Bazel version in downstream pipelines. This means that two tasks that
        # only differ in the value of their explicit "bazel" field will be identical in the
        # downstream pipeline, thus leading to duplicate work.
        # Consequently, we filter those duplicate tasks here.
        if is_downstream_project:
            h = hash_task_config(task, task_config)
            if h in config_hashes:
                continue
            config_hashes.add(h)

        shards = task_config.get("shards", "1")
        try:
            shards = int(shards)
        except ValueError:
            raise BuildkiteException("Task {} has invalid shard value '{}'".format(task, shards))

        step = runner_step(
            platform=get_platform_for_task(task, task_config),
            task=task,
            task_name=task_config.get("name"),
            project_name=project_name,
            http_config=http_config,
            file_config=file_config,
            git_repository=git_repository,
            git_commit=git_commit,
            monitor_flaky_tests=monitor_flaky_tests,
            use_but=use_but,
            incompatible_flags=incompatible_flags,
            shards=shards,
        )
        pipeline_steps.append(step)

    pipeline_slug = os.getenv("BUILDKITE_PIPELINE_SLUG")
    all_downstream_pipeline_slugs = []
    for _, config in DOWNSTREAM_PROJECTS.items():
        all_downstream_pipeline_slugs.append(config["pipeline_slug"])
    # We don't need to update last green commit in the following cases:
    #   1. This job is a GitHub pull request
    #   2. This job uses a custom built Bazel binary (in Bazel Downstream Projects pipeline)
    #   3. This job doesn't run on master branch (could be a custom build launched manually)
    #   4. We don't intend to run the same job in downstream with Bazel@HEAD (eg. google-bazel-presubmit)
    #   5. We are testing incompatible flags
    if not (
        is_pull_request()
        or use_but
        or os.getenv("BUILDKITE_BRANCH") != "master"
        or pipeline_slug not in all_downstream_pipeline_slugs
        or incompatible_flags
    ):
        # We need to call "Try Update Last Green Commit" even if there are failures,
        # since we don't want a failing Buildifier step to block the update of
        # the last green commit for this project.
        # try_update_last_green_commit() ensures that we don't update the commit
        # if any build or test steps fail.
        pipeline_steps.append({"wait": None, "continue_on_failure": True})
        pipeline_steps.append(
            create_step(
                label="Try Update Last Green Commit",
                commands=[
                    fetch_bazelcipy_command(),
                    PLATFORMS[DEFAULT_PLATFORM]["python"]
                    + " bazelci.py try_update_last_green_commit",
                ],
                platform=DEFAULT_PLATFORM,
            )
        )

    if "validate_config" in configs:
        pipeline_steps += create_config_validation_steps()

    print_pipeline_steps(pipeline_steps, handle_emergencies=not is_downstream_project)


def hash_task_config(task_name, task_config):
    # Two task configs c1 and c2 have the same hash iff they lead to two functionally identical jobs
    # in the downstream pipeline. This function discards the "bazel" field (since it's being
    # overriden) and the "name" field (since it has no effect on the actual work).
    # Moreover, it adds an explicit "platform" field if that's missing.
    cpy = task_config.copy()
    cpy.pop("bazel", None)
    cpy.pop("name", None)
    if "platform" not in cpy:
        cpy["platform"] = task_name

    m = hashlib.md5()
    for key in sorted(cpy):
        value = "%s:%s;" % (key, cpy[key])
        m.update(value.encode("utf-8"))

    return m.digest()


def get_platform_for_task(task, task_config):
    # Most pipeline configurations have exactly one task per platform, which makes it
    # convenient to use the platform name as task ID. Consequently, we use the
    # task ID as platform if there is no explicit "platform" field.
    return task_config.get("platform", task)


def create_config_validation_steps():
    output = execute_command_and_get_output(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", os.getenv("BUILDKITE_COMMIT")]
    )
    config_files = [
        l
        for l in output.split("\n")
        if l.startswith(".bazelci/") and os.path.splitext(l)[1] in CONFIG_FILE_EXTENSIONS
    ]
    return [
        create_step(
            label=":cop: Validate {}".format(f),
            commands=[
                fetch_bazelcipy_command(),
                "{} bazelci.py project_pipeline --file_config={}".format(
                    PLATFORMS[DEFAULT_PLATFORM]["python"], f
                ),
            ],
            platform=DEFAULT_PLATFORM,
        )
        for f in config_files
    ]


def print_pipeline_steps(pipeline_steps, handle_emergencies=True):
    if handle_emergencies:
        emergency_step = create_emergency_announcement_step_if_necessary()
        if emergency_step:
            pipeline_steps.insert(0, emergency_step)

    print(yaml.dump({"steps": pipeline_steps}))


def create_emergency_announcement_step_if_necessary():
    style = "error"
    message, issue_url, last_good_bazel = None, None, None
    try:
        emergency_settings = load_remote_yaml_file(EMERGENCY_FILE_URL)
        message = emergency_settings.get("message")
        issue_url = emergency_settings.get("issue_url")
        last_good_bazel = emergency_settings.get("last_good_bazel")
    except urllib.error.HTTPError as ex:
        message = str(ex)
        style = "warning"

    if not any([message, issue_url, last_good_bazel]):
        return

    text = '<span class="h1">:rotating_light: Emergency :rotating_light:</span>\n'
    if message:
        text += "- {}\n".format(message)
    if issue_url:
        text += '- Please check this <a href="{}">issue</a> for more details.\n'.format(issue_url)
    if last_good_bazel:
        text += (
            "- Default Bazel version is *{}*, "
            "unless the pipeline configuration specifies an explicit version."
        ).format(last_good_bazel)

    return create_step(
        label=":rotating_light: Emergency :rotating_light:",
        commands=[
            'buildkite-agent annotate --append --style={} --context "omg" "{}"'.format(style, text)
        ],
        platform=DEFAULT_PLATFORM,
    )


def runner_step(
    platform,
    task,
    task_name=None,
    project_name=None,
    http_config=None,
    file_config=None,
    git_repository=None,
    git_commit=None,
    monitor_flaky_tests=False,
    use_but=False,
    incompatible_flags=None,
    shards=1,
):
    command = PLATFORMS[platform]["python"] + " bazelci.py runner --task=" + task
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
    for flag in incompatible_flags or []:
        command += " --incompatible_flag=" + flag
    label = create_label(platform, project_name, task_name=task_name)
    return create_step(
        label=label, commands=[fetch_bazelcipy_command(), command], platform=platform, shards=shards
    )


def fetch_bazelcipy_command():
    return "curl -sS {0} -o bazelci.py".format(SCRIPT_URL)


def fetch_incompatible_flag_verbose_failures_command():
    return "curl -sS {0} -o incompatible_flag_verbose_failures.py".format(
        INCOMPATIBLE_FLAG_VERBOSE_FAILURES_URL
    )


def fetch_aggregate_incompatible_flags_test_result_command():
    return "curl -sS {0} -o aggregate_incompatible_flags_test_result.py".format(
        AGGREGATE_INCOMPATIBLE_TEST_RESULT_URL
    )


def upload_project_pipeline_step(
    project_name, git_repository, http_config, file_config, incompatible_flags
):
    pipeline_command = (
        '{0} bazelci.py project_pipeline --project_name="{1}" ' + "--git_repository={2}"
    ).format(PLATFORMS[DEFAULT_PLATFORM]["python"], project_name, git_repository)
    if incompatible_flags is None:
        pipeline_command += " --use_but"
    else:
        for flag in incompatible_flags:
            pipeline_command += " --incompatible_flag=" + flag
    if http_config:
        pipeline_command += " --http_config=" + http_config
    if file_config:
        pipeline_command += " --file_config=" + file_config
    pipeline_command += " | buildkite-agent pipeline upload"

    return create_step(
        label="Setup {0}".format(project_name),
        commands=[fetch_bazelcipy_command(), pipeline_command],
        platform=DEFAULT_PLATFORM,
    )


def create_label(platform, project_name, build_only=False, test_only=False, task_name=None):
    if build_only and test_only:
        raise BuildkiteException("build_only and test_only cannot be true at the same time")
    platform_display_name = PLATFORMS[platform]["emoji-name"]

    if build_only:
        label = "Build "
    elif test_only:
        label = "Test "
    else:
        label = ""

    platform_label = (
        "{0} on {1}".format(task_name, platform_display_name)
        if task_name
        else platform_display_name
    )

    if project_name:
        label += "{0} ({1})".format(project_name, platform_label)
    else:
        label += platform_label

    return label


def bazel_build_step(
    task,
    platform,
    project_name,
    http_config=None,
    file_config=None,
    build_only=False,
    test_only=False,
):
    pipeline_command = PLATFORMS[platform]["python"] + " bazelci.py runner"
    if build_only:
        pipeline_command += " --build_only --save_but"
    if test_only:
        pipeline_command += " --test_only"
    if http_config:
        pipeline_command += " --http_config=" + http_config
    if file_config:
        pipeline_command += " --file_config=" + file_config
    pipeline_command += " --task=" + task

    return create_step(
        label=create_label(platform, project_name, build_only, test_only),
        commands=[fetch_bazelcipy_command(), pipeline_command],
        platform=platform,
    )


def filter_tasks_that_should_be_skipped(task_configs, pipeline_steps):
    skip_tasks = get_skip_tasks()
    if not skip_tasks:
        return task_configs

    actually_skipped = []
    skip_tasks = set(skip_tasks)
    for task in list(task_configs.keys()):
        if task in skip_tasks:
            actually_skipped.append(task)
            del task_configs[task]
            skip_tasks.remove(task)

    if not task_configs:
        raise BuildkiteException(
            "Nothing to do since all tasks in the configuration should be skipped."
        )

    annotations = []
    if actually_skipped:
        annotations.append(
            ("info", "Skipping the following task(s): {}".format(", ".join(actually_skipped)))
        )

    if skip_tasks:
        annotations.append(
            (
                "warning",
                (
                    "The following tasks should have been skipped, "
                    "but were not part of the configuration: {}"
                ).format(", ".join(skip_tasks)),
            )
        )

    if annotations:
        print_skip_task_annotations(annotations, pipeline_steps)

    return task_configs


def get_skip_tasks():
    value = os.getenv(SKIP_TASKS_ENV_VAR, "")
    return [v for v in value.split(",") if v]


def print_skip_task_annotations(annotations, pipeline_steps):
    commands = [
        "buildkite-agent annotate --style={} '{}'  --context 'ctx-{}'".format(s, t, hash(t))
        for s, t in annotations
    ]
    pipeline_steps.append(
        create_step(
            label=":pipeline: Print information about skipped tasks",
            commands=commands,
            platform=DEFAULT_PLATFORM,
        )
    )


def print_bazel_publish_binaries_pipeline(task_configs, http_config, file_config):
    if not task_configs:
        raise BuildkiteException("Bazel publish binaries pipeline configuration is empty.")

    pipeline_steps = []
    task_configs = filter_tasks_that_should_be_skipped(task_configs, pipeline_steps)

    platforms = [get_platform_for_task(t, tc) for t, tc in task_configs.items()]

    # These are the platforms that the bazel_publish_binaries.yml config is actually building.
    configured_platforms = set(filter(should_publish_binaries_for_platform, platforms))

    # These are the platforms that we want to build and publish according to this script.
    expected_platforms = set(filter(should_publish_binaries_for_platform, PLATFORMS))

    if not expected_platforms.issubset(configured_platforms):
        raise BuildkiteException(
            "Bazel publish binaries pipeline needs to build Bazel for every commit on all publish_binary-enabled platforms."
        )

    # Build Bazel
    for task, task_config in task_configs.items():
        pipeline_steps.append(
            bazel_build_step(
                task,
                get_platform_for_task(task, task_config),
                "Bazel",
                http_config,
                file_config,
                build_only=True,
            )
        )

    pipeline_steps.append("wait")

    # If all builds succeed, publish the Bazel binaries to GCS.
    pipeline_steps.append(
        create_step(
            label="Publish Bazel Binaries",
            commands=[
                fetch_bazelcipy_command(),
                PLATFORMS[DEFAULT_PLATFORM]["python"] + " bazelci.py publish_binaries",
            ],
            platform=DEFAULT_PLATFORM,
        )
    )

    print_pipeline_steps(pipeline_steps)


def should_publish_binaries_for_platform(platform):
    if platform not in PLATFORMS:
        raise BuildkiteException("Unknown platform '{}'".format(platform))

    return PLATFORMS[platform]["publish_binary"]


def print_disabled_projects_info_box_step():
    info_text = ["Downstream testing is disabled for the following projects :sadpanda:"]
    for project, config in DOWNSTREAM_PROJECTS.items():
        disabled_reason = config.get("disabled_reason", None)
        if disabled_reason:
            info_text.append("* **%s**: %s" % (project, disabled_reason))

    if len(info_text) == 1:
        return None
    return create_step(
        label=":sadpanda:",
        commands=[
            'buildkite-agent annotate --append --style=info "\n' + "\n".join(info_text) + '\n"'
        ],
        platform=DEFAULT_PLATFORM,
    )


def print_incompatible_flags_info_box_step(incompatible_flags_map):
    info_text = ["Build and test with the following incompatible flags:"]

    for flag in incompatible_flags_map:
        info_text.append("* **%s**: %s" % (flag, incompatible_flags_map[flag]))

    if len(info_text) == 1:
        return None
    return create_step(
        label="Incompatible flags info",
        commands=[
            'buildkite-agent annotate --append --style=info "\n' + "\n".join(info_text) + '\n"'
        ],
        platform=DEFAULT_PLATFORM,
    )


def fetch_incompatible_flags():
    """
    Return a list of incompatible flags to be tested in downstream with the current release Bazel
    """
    incompatible_flags = {}

    # If INCOMPATIBLE_FLAGS environment variable is set, we get incompatible flags from it.
    if "INCOMPATIBLE_FLAGS" in os.environ:
        for flag in os.environ["INCOMPATIBLE_FLAGS"].split():
            # We are not able to get the github link for this flag from INCOMPATIBLE_FLAGS,
            # so just assign the url to empty string.
            incompatible_flags[flag] = ""
        return incompatible_flags

    # Get bazel major version on CI, eg. 0.21 from "Build label: 0.21.0\n..."
    output = subprocess.check_output(
        ["bazel", "--nomaster_bazelrc", "--bazelrc=/dev/null", "version"]
    ).decode("utf-8")
    bazel_major_version = output.split()[2].rsplit(".", 1)[0]

    output = subprocess.check_output(
        [
            "curl",
            "https://api.github.com/search/issues?per_page=100&q=repo:bazelbuild/bazel+label:migration-%s+state:open"
            % bazel_major_version,
        ]
    ).decode("utf-8")
    issue_info = json.loads(output)

    for issue in issue_info["items"]:
        # Every incompatible flags issue should start with "<incompatible flag name (without --)>:"
        name = "--" + issue["title"].split(":")[0]
        url = issue["html_url"]
        if name.startswith("--incompatible_"):
            incompatible_flags[name] = url
        else:
            eprint(
                f"{name} is not recognized as an incompatible flag, please modify the issue title "
                f'of {url} to "<incompatible flag name (without --)>:..."'
            )

    return incompatible_flags


def print_bazel_downstream_pipeline(
    task_configs, http_config, file_config, test_incompatible_flags, test_disabled_projects
):
    if not task_configs:
        raise BuildkiteException("Bazel downstream pipeline configuration is empty.")

    pipeline_steps = []
    task_configs = filter_tasks_that_should_be_skipped(task_configs, pipeline_steps)

    configured_platforms = set(get_platform_for_task(t, c) for t, c in task_configs.items())
    if configured_platforms != set(PLATFORMS):
        raise BuildkiteException(
            "Bazel downstream pipeline needs to build Bazel on all supported platforms (has=%s vs. want=%s)."
            % (sorted(configured_platforms), sorted(set(PLATFORMS)))
        )

    pipeline_steps = []

    info_box_step = print_disabled_projects_info_box_step()
    if info_box_step is not None:
        pipeline_steps.append(info_box_step)

    if not test_incompatible_flags:
        for task, task_config in task_configs.items():
            pipeline_steps.append(
                bazel_build_step(
                    task,
                    get_platform_for_task(task, task_config),
                    "Bazel",
                    http_config,
                    file_config,
                    build_only=True,
                )
            )

        pipeline_steps.append("wait")

    incompatible_flags = None
    if test_incompatible_flags:
        incompatible_flags_map = fetch_incompatible_flags()
        info_box_step = print_incompatible_flags_info_box_step(incompatible_flags_map)
        if info_box_step is not None:
            pipeline_steps.append(info_box_step)
        incompatible_flags = list(incompatible_flags_map.keys())

    for project, config in DOWNSTREAM_PROJECTS.items():
        disabled_reason = config.get("disabled_reason", None)
        # If test_disabled_projects is true, we add configs for disabled projects.
        # If test_disabled_projects is false, we add configs for not disabled projects.
        if (test_disabled_projects and disabled_reason) or (
            not test_disabled_projects and not disabled_reason
        ):
            pipeline_steps.append(
                upload_project_pipeline_step(
                    project_name=project,
                    git_repository=config["git_repository"],
                    http_config=config.get("http_config", None),
                    file_config=config.get("file_config", None),
                    incompatible_flags=incompatible_flags,
                )
            )

    if test_incompatible_flags:
        current_build_number = os.environ.get("BUILDKITE_BUILD_NUMBER", None)
        if not current_build_number:
            raise BuildkiteException("Not running inside Buildkite")
        if use_bazelisk_migrate():
            pipeline_steps.append({"wait": "~", "continue_on_failure": "true"})
            pipeline_steps.append(
                create_step(
                    label="Aggregate incompatible flags test result",
                    commands=[
                        fetch_bazelcipy_command(),
                        fetch_aggregate_incompatible_flags_test_result_command(),
                        PLATFORMS[DEFAULT_PLATFORM]["python"]
                        + " aggregate_incompatible_flags_test_result.py --build_number=%s"
                        % current_build_number,
                    ],
                    platform=DEFAULT_PLATFORM,
                )
            )
        else:
            pipeline_steps.append({"wait": "~", "continue_on_failure": "true"})
            pipeline_steps.append(
                create_step(
                    label="Test failing jobs with incompatible flag separately",
                    commands=[
                        fetch_bazelcipy_command(),
                        fetch_incompatible_flag_verbose_failures_command(),
                        PLATFORMS[DEFAULT_PLATFORM]["python"]
                        + " incompatible_flag_verbose_failures.py --build_number=%s | buildkite-agent pipeline upload"
                        % current_build_number,
                    ],
                    platform=DEFAULT_PLATFORM,
                )
            )

    if (
        not test_disabled_projects
        and not test_incompatible_flags
        and os.getenv("BUILDKITE_BRANCH") == "master"
    ):
        # Only update the last green downstream commit in the regular Bazel@HEAD + Downstream pipeline.
        pipeline_steps.append("wait")
        pipeline_steps.append(
            create_step(
                label="Try Update Last Green Downstream Commit",
                commands=[
                    fetch_bazelcipy_command(),
                    PLATFORMS[DEFAULT_PLATFORM]["python"]
                    + " bazelci.py try_update_last_green_downstream_commit",
                ],
                platform=DEFAULT_PLATFORM,
            )
        )

    print_pipeline_steps(pipeline_steps)


def bazelci_builds_download_url(platform, git_commit):
    bucket_name = "bazel-testing-builds" if THIS_IS_TESTING else "bazel-builds"
    return "https://storage.googleapis.com/{}/artifacts/{}/{}/bazel".format(
        bucket_name, platform, git_commit
    )


def bazelci_builds_gs_url(platform, git_commit):
    bucket_name = "bazel-testing-builds" if THIS_IS_TESTING else "bazel-builds"
    return "gs://{}/artifacts/{}/{}/bazel".format(bucket_name, platform, git_commit)


def bazelci_builds_metadata_url():
    bucket_name = "bazel-testing-builds" if THIS_IS_TESTING else "bazel-builds"
    return "gs://{}/metadata/latest.json".format(bucket_name)


def bazelci_last_green_commit_url(git_repository, pipeline_slug):
    bucket_name = "bazel-testing-builds" if THIS_IS_TESTING else "bazel-untrusted-builds"
    return "gs://{}/last_green_commit/{}/{}".format(
        bucket_name, git_repository[len("https://") :], pipeline_slug
    )


def bazelci_last_green_downstream_commit_url():
    bucket_name = "bazel-testing-builds" if THIS_IS_TESTING else "bazel-untrusted-builds"
    return "gs://{}/last_green_commit/downstream_pipeline".format(bucket_name)


def get_last_green_commit(last_green_commit_url):
    try:
        return (
            subprocess.check_output(
                [gsutil_command(), "cat", last_green_commit_url], env=os.environ
            )
            .decode("utf-8")
            .strip()
        )
    except subprocess.CalledProcessError:
        return None


def try_update_last_green_commit():
    org_slug = os.getenv("BUILDKITE_ORGANIZATION_SLUG")
    pipeline_slug = os.getenv("BUILDKITE_PIPELINE_SLUG")
    build_number = os.getenv("BUILDKITE_BUILD_NUMBER")
    current_job_id = os.getenv("BUILDKITE_JOB_ID")

    client = BuildkiteClient(org=org_slug, pipeline=pipeline_slug)
    build_info = client.get_build_info(build_number)

    # Find any failing steps other than Buildifier and "try update last green".
    def HasFailed(job):
        state = job.get("state")
        # Ignore steps that don't have a state (like "wait").
        return (
            state is not None
            and state != "passed"
            and job["id"] != current_job_id
            and job["name"] != BUILDIFIER_STEP_NAME
        )

    failing_jobs = [j["name"] for j in build_info["jobs"] if HasFailed(j)]
    if failing_jobs:
        raise BuildkiteException(
            "Cannot update last green commit due to {} failing step(s): {}".format(
                len(failing_jobs), ", ".join(failing_jobs)
            )
        )

    git_repository = os.getenv("BUILDKITE_REPO")
    last_green_commit_url = bazelci_last_green_commit_url(git_repository, pipeline_slug)
    update_last_green_commit_if_newer(last_green_commit_url)


def update_last_green_commit_if_newer(last_green_commit_url):
    last_green_commit = get_last_green_commit(last_green_commit_url)
    current_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    if last_green_commit:
        execute_command(["git", "fetch", "-v", "origin", last_green_commit])
        result = (
            subprocess.check_output(
                ["git", "rev-list", "%s..%s" % (last_green_commit, current_commit)]
            )
            .decode("utf-8")
            .strip()
        )

    # If current_commit is newer that last_green_commit, `git rev-list A..B` will output a bunch of
    # commits, otherwise the output should be empty.
    if not last_green_commit or result:
        execute_command(
            ["echo %s | %s cp - %s" % (current_commit, gsutil_command(), last_green_commit_url)],
            shell=True,
        )
    else:
        eprint(
            "Updating abandoned: last green commit (%s) is not older than current commit (%s)."
            % (last_green_commit, current_commit)
        )


def try_update_last_green_downstream_commit():
    last_green_commit_url = bazelci_last_green_downstream_commit_url()
    update_last_green_commit_if_newer(last_green_commit_url)


def latest_generation_and_build_number():
    output = None
    attempt = 0
    while attempt < 5:
        output = subprocess.check_output(
            [gsutil_command(), "stat", bazelci_builds_metadata_url()], env=os.environ
        )
        match = re.search("Generation:[ ]*([0-9]+)", output.decode("utf-8"))
        if not match:
            raise BuildkiteException("Couldn't parse generation. gsutil output format changed?")
        generation = match.group(1)

        match = re.search(r"Hash \(md5\):[ ]*([^\s]+)", output.decode("utf-8"))
        if not match:
            raise BuildkiteException("Couldn't parse md5 hash. gsutil output format changed?")
        expected_md5hash = base64.b64decode(match.group(1))

        output = subprocess.check_output(
            [gsutil_command(), "cat", bazelci_builds_metadata_url()], env=os.environ
        )
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


def upload_bazel_binaries():
    """
    Uploads all Bazel binaries to a deterministic URL based on the current Git commit.

    Returns a map of platform names to sha256 hashes of the corresponding Bazel binary.
    """
    hashes = {}
    for platform_name, platform in PLATFORMS.items():
        if not should_publish_binaries_for_platform(platform_name):
            continue
        tmpdir = tempfile.mkdtemp()
        try:
            bazel_binary_path = download_bazel_binary(tmpdir, platform_name)
            # One platform that we build on can generate binaries for multiple platforms, e.g.
            # the ubuntu1604 platform generates binaries for the "ubuntu1604" platform, but also
            # for the generic "linux" platform.
            for target_platform_name in platform["publish_binary"]:
                execute_command(
                    [
                        gsutil_command(),
                        "cp",
                        bazel_binary_path,
                        bazelci_builds_gs_url(target_platform_name, os.environ["BUILDKITE_COMMIT"]),
                    ]
                )
                hashes[target_platform_name] = sha256_hexdigest(bazel_binary_path)
        finally:
            shutil.rmtree(tmpdir)
    return hashes


def try_publish_binaries(hashes, build_number, expected_generation):
    """
    Uploads the info.json file that contains information about the latest Bazel commit that was
    successfully built on CI.
    """
    now = datetime.datetime.now()
    git_commit = os.environ["BUILDKITE_COMMIT"]
    info = {
        "build_number": build_number,
        "build_time": now.strftime("%d-%m-%Y %H:%M"),
        "git_commit": git_commit,
        "platforms": {},
    }
    for platform, sha256 in hashes.items():
        info["platforms"][platform] = {
            "url": bazelci_builds_download_url(platform, git_commit),
            "sha256": sha256,
        }
    tmpdir = tempfile.mkdtemp()
    try:
        info_file = os.path.join(tmpdir, "info.json")
        with open(info_file, mode="w", encoding="utf-8") as fp:
            json.dump(info, fp, indent=2, sort_keys=True)

        try:
            execute_command(
                [
                    gsutil_command(),
                    "-h",
                    "x-goog-if-generation-match:" + expected_generation,
                    "-h",
                    "Content-Type:application/json",
                    "cp",
                    info_file,
                    bazelci_builds_metadata_url(),
                ]
            )
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

    # Upload the Bazel binaries for this commit.
    hashes = upload_bazel_binaries()

    # Try to update the info.json with data about our build. This will fail (expectedly) if we're
    # not the latest build.
    for _ in range(5):
        latest_generation, latest_build_number = latest_generation_and_build_number()

        if current_build_number <= latest_build_number:
            eprint(
                (
                    "Current build '{0}' is not newer than latest published '{1}'. "
                    + "Skipping publishing of binaries."
                ).format(current_build_number, latest_build_number)
            )
            break

        try:
            try_publish_binaries(hashes, current_build_number, latest_generation)
        except BinaryUploadRaceException:
            # Retry.
            continue

        eprint(
            "Successfully updated '{0}' to binaries from build {1}.".format(
                bazelci_builds_metadata_url(), current_build_number
            )
        )
        break
    else:
        raise BuildkiteException("Could not publish binaries, ran out of attempts.")


# This is so that multiline python strings are represented as YAML
# block strings.
def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    yaml.add_representer(str, str_presenter)

    parser = argparse.ArgumentParser(description="Bazel Continuous Integration Script")
    parser.add_argument("--script", type=str)

    subparsers = parser.add_subparsers(dest="subparsers_name")

    bazel_publish_binaries_pipeline = subparsers.add_parser("bazel_publish_binaries_pipeline")
    bazel_publish_binaries_pipeline.add_argument("--file_config", type=str)
    bazel_publish_binaries_pipeline.add_argument("--http_config", type=str)
    bazel_publish_binaries_pipeline.add_argument("--git_repository", type=str)

    bazel_downstream_pipeline = subparsers.add_parser("bazel_downstream_pipeline")
    bazel_downstream_pipeline.add_argument("--file_config", type=str)
    bazel_downstream_pipeline.add_argument("--http_config", type=str)
    bazel_downstream_pipeline.add_argument("--git_repository", type=str)
    bazel_downstream_pipeline.add_argument(
        "--test_incompatible_flags", type=bool, nargs="?", const=True
    )
    bazel_downstream_pipeline.add_argument(
        "--test_disabled_projects", type=bool, nargs="?", const=True
    )

    project_pipeline = subparsers.add_parser("project_pipeline")
    project_pipeline.add_argument("--project_name", type=str)
    project_pipeline.add_argument("--file_config", type=str)
    project_pipeline.add_argument("--http_config", type=str)
    project_pipeline.add_argument("--git_repository", type=str)
    project_pipeline.add_argument("--monitor_flaky_tests", type=bool, nargs="?", const=True)
    project_pipeline.add_argument("--use_but", type=bool, nargs="?", const=True)
    project_pipeline.add_argument("--incompatible_flag", type=str, action="append")

    runner = subparsers.add_parser("runner")
    runner.add_argument("--task", action="store", type=str, default="")
    runner.add_argument("--file_config", type=str)
    runner.add_argument("--http_config", type=str)
    runner.add_argument("--git_repository", type=str)
    runner.add_argument(
        "--git_commit", type=str, help="Reset the git repository to this commit after cloning it"
    )
    runner.add_argument(
        "--git_repo_location",
        type=str,
        help="Use an existing repository instead of cloning from github",
    )
    runner.add_argument(
        "--use_bazel_at_commit", type=str, help="Use Bazel binary built at a specific commit"
    )
    runner.add_argument("--use_but", type=bool, nargs="?", const=True)
    runner.add_argument("--save_but", type=bool, nargs="?", const=True)
    runner.add_argument("--needs_clean", type=bool, nargs="?", const=True)
    runner.add_argument("--build_only", type=bool, nargs="?", const=True)
    runner.add_argument("--test_only", type=bool, nargs="?", const=True)
    runner.add_argument("--monitor_flaky_tests", type=bool, nargs="?", const=True)
    runner.add_argument("--incompatible_flag", type=str, action="append")

    runner = subparsers.add_parser("publish_binaries")

    runner = subparsers.add_parser("try_update_last_green_commit")
    runner = subparsers.add_parser("try_update_last_green_downstream_commit")

    args = parser.parse_args(argv)

    if args.script:
        global SCRIPT_URL
        SCRIPT_URL = args.script

    try:
        if args.subparsers_name == "bazel_publish_binaries_pipeline":
            configs = fetch_configs(args.http_config, args.file_config)
            print_bazel_publish_binaries_pipeline(
                task_configs=configs.get("tasks", None),
                http_config=args.http_config,
                file_config=args.file_config,
            )
        elif args.subparsers_name == "bazel_downstream_pipeline":
            configs = fetch_configs(args.http_config, args.file_config)
            print_bazel_downstream_pipeline(
                task_configs=configs.get("tasks", None),
                http_config=args.http_config,
                file_config=args.file_config,
                test_incompatible_flags=args.test_incompatible_flags,
                test_disabled_projects=args.test_disabled_projects,
            )
        elif args.subparsers_name == "project_pipeline":
            configs = fetch_configs(args.http_config, args.file_config)
            print_project_pipeline(
                configs=configs,
                project_name=args.project_name,
                http_config=args.http_config,
                file_config=args.file_config,
                git_repository=args.git_repository,
                monitor_flaky_tests=args.monitor_flaky_tests,
                use_but=args.use_but,
                incompatible_flags=args.incompatible_flag,
            )
        elif args.subparsers_name == "runner":
            configs = fetch_configs(args.http_config, args.file_config)
            tasks = configs.get("tasks", {})
            task_config = tasks.get(args.task)
            if not task_config:
                raise BuildkiteException(
                    "No such task '{}' in configuration. Available: {}".format(
                        args.task, ", ".join(tasks)
                    )
                )

            platform = get_platform_for_task(args.task, task_config)

            execute_commands(
                task_config=task_config,
                platform=platform,
                git_repository=args.git_repository,
                git_commit=args.git_commit,
                git_repo_location=args.git_repo_location,
                use_bazel_at_commit=args.use_bazel_at_commit,
                use_but=args.use_but,
                save_but=args.save_but,
                needs_clean=args.needs_clean,
                build_only=args.build_only,
                test_only=args.test_only,
                monitor_flaky_tests=args.monitor_flaky_tests,
                incompatible_flags=args.incompatible_flag,
                bazel_version=task_config.get("bazel") or configs.get("bazel"),
            )
        elif args.subparsers_name == "publish_binaries":
            publish_binaries()
        elif args.subparsers_name == "try_update_last_green_commit":
            # Update the last green commit of a project pipeline
            try_update_last_green_commit()
        elif args.subparsers_name == "try_update_last_green_downstream_commit":
            # Update the last green commit of the downstream pipeline
            try_update_last_green_downstream_commit()
        else:
            parser.print_help()
            return 2
    except BuildkiteException as e:
        eprint(str(e))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
