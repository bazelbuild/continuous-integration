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
import copy
import datetime
from glob import glob
import hashlib
import itertools
import json
import multiprocessing
import os
import os.path
import platform as platform_module
import random
import re
import requests
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import yaml

# Initialize the random number generator.
random.seed()

BUILDKITE_ORG = os.environ["BUILDKITE_ORGANIZATION_SLUG"]
THIS_IS_PRODUCTION = BUILDKITE_ORG == "bazel"
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

KZIPS_BUCKET = {
    "bazel-testing": "gs://bazel-kzips-testing/",
    "bazel-trusted": "gs://bazel-kzips/",
    "bazel": "gs://bazel-kzips/",
}[BUILDKITE_ORG]

# Projects can opt out of receiving GitHub issues from --notify by adding `"do_not_notify": True` to their respective downstream entry.
DOWNSTREAM_PROJECTS_PRODUCTION = {
    "Android Studio Plugin": {
        "git_repository": "https://github.com/bazelbuild/intellij.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/intellij/master/.bazelci/android-studio.yml",
        "pipeline_slug": "android-studio-plugin",
    },
    "Android Studio Plugin Google": {
        "git_repository": "https://github.com/bazelbuild/intellij.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/intellij/google/.bazelci/android-studio.yml",
        "pipeline_slug": "android-studio-plugin-google",
    },
    "Android Testing": {
        "git_repository": "https://github.com/googlesamples/android-testing.git",
        "http_config": "https://raw.githubusercontent.com/googlesamples/android-testing/master/bazelci/buildkite-pipeline.yml",
        "pipeline_slug": "android-testing",
        "disabled_reason": "https://github.com/android/testing-samples/issues/417",
    },
    "Bazel": {
        "git_repository": "https://github.com/bazelbuild/bazel.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/bazel/master/.bazelci/postsubmit.yml",
        "pipeline_slug": "bazel-bazel",
    },
    "Bazel (with Bzlmod)": {
        "git_repository": "https://github.com/bazelbuild/bazel.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/bazel/master/.bazelci/postsubmit_bzlmod.yml",
        "pipeline_slug": "bazel-bazel-with-bzlmod",
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
        "disabled_reason": "https://github.com/bazelbuild/codelabs/issues/38",
    },
    "Bazel Examples": {
        "git_repository": "https://github.com/bazelbuild/examples.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/examples/master/.bazelci/presubmit.yml",
        "pipeline_slug": "bazel-bazel-examples",
    },
    "Bazel Remote Cache": {
        "git_repository": "https://github.com/buchgr/bazel-remote.git",
        "http_config": "https://raw.githubusercontent.com/buchgr/bazel-remote/master/.bazelci/presubmit.yml",
        "pipeline_slug": "bazel-remote-cache",
    },
    "Bazel skylib": {
        "git_repository": "https://github.com/bazelbuild/bazel-skylib.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/bazel-skylib/main/.bazelci/presubmit.yml",
        "pipeline_slug": "bazel-skylib",
        "owned_by_bazel": True,
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
        "http_config": "https://raw.githubusercontent.com/bazelbuild/bazel-buildfarm/main/.bazelci/presubmit.yml",
        "pipeline_slug": "buildfarm-farmer",
    },
    "Buildtools": {
        "git_repository": "https://github.com/bazelbuild/buildtools.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/buildtools/master/.bazelci/presubmit.yml",
        "pipeline_slug": "buildtools",
    },
    "Cargo-Raze": {
        "git_repository": "https://github.com/google/cargo-raze.git",
        "http_config": "https://raw.githubusercontent.com/google/cargo-raze/main/.bazelci/presubmit.yml",
        "pipeline_slug": "cargo-raze",
    },
    "CLion Plugin": {
        "git_repository": "https://github.com/bazelbuild/intellij.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/intellij/master/.bazelci/clion.yml",
        "pipeline_slug": "clion-plugin",
    },
    "CLion Plugin Google": {
        "git_repository": "https://github.com/bazelbuild/intellij.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/intellij/google/.bazelci/clion.yml",
        "pipeline_slug": "clion-plugin-google",
    },
    "Cartographer": {
        "git_repository": "https://github.com/googlecartographer/cartographer.git",
        "http_config": "https://raw.githubusercontent.com/googlecartographer/cartographer/master/.bazelci/presubmit.yml",
        "pipeline_slug": "cartographer",
    },
    "Cloud Robotics Core": {
        "git_repository": "https://github.com/googlecloudrobotics/core.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/cloud-robotics.yml",
        "pipeline_slug": "cloud-robotics-core",
    },
    "Envoy": {
        "git_repository": "https://github.com/envoyproxy/envoy.git",
        "http_config": "https://raw.githubusercontent.com/envoyproxy/envoy/main/.bazelci/presubmit.yml",
        "pipeline_slug": "envoy",
    },
    "FlatBuffers": {
        "git_repository": "https://github.com/google/flatbuffers.git",
        "http_config": "https://raw.githubusercontent.com/google/flatbuffers/master/.bazelci/presubmit.yml",
        "pipeline_slug": "flatbuffers",
    },
    "Flogger": {
        "git_repository": "https://github.com/google/flogger.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/flogger.yml",
        "pipeline_slug": "flogger",
    },
    "Gerrit": {
        "git_repository": "https://gerrit.googlesource.com/gerrit.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/gerrit.yml",
        "pipeline_slug": "gerrit",
    },
    "Google Logging": {
        "git_repository": "https://github.com/google/glog.git",
        "http_config": "https://raw.githubusercontent.com/google/glog/master/.bazelci/presubmit.yml",
        "pipeline_slug": "google-logging",
    },
    "IntelliJ Plugin": {
        "git_repository": "https://github.com/bazelbuild/intellij.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/intellij/master/.bazelci/intellij.yml",
        "pipeline_slug": "intellij-plugin",
    },
    "IntelliJ Plugin Google": {
        "git_repository": "https://github.com/bazelbuild/intellij.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/intellij/google/.bazelci/intellij.yml",
        "pipeline_slug": "intellij-plugin-google",
    },
    "IntelliJ UE Plugin": {
        "git_repository": "https://github.com/bazelbuild/intellij.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/intellij/master/.bazelci/intellij-ue.yml",
        "pipeline_slug": "intellij-ue-plugin",
    },
    "IntelliJ UE Plugin Google": {
        "git_repository": "https://github.com/bazelbuild/intellij.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/intellij/google/.bazelci/intellij-ue.yml",
        "pipeline_slug": "intellij-ue-plugin-google",
    },
    "IntelliJ Plugin Aspect": {
        "git_repository": "https://github.com/bazelbuild/intellij.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/intellij/master/.bazelci/aspect.yml",
        "pipeline_slug": "intellij-plugin-aspect",
    },
    "IntelliJ Plugin Aspect Google": {
        "git_repository": "https://github.com/bazelbuild/intellij.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/intellij/google/.bazelci/aspect.yml",
        "pipeline_slug": "intellij-plugin-aspect-google",
    },
    "Kythe": {
        "git_repository": "https://github.com/kythe/kythe.git",
        "http_config": "https://raw.githubusercontent.com/kythe/kythe/master/.bazelci/presubmit.yml",
        "pipeline_slug": "kythe",
    },
    "Protobuf": {
        "git_repository": "https://github.com/google/protobuf.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/protobuf.yml",
        "pipeline_slug": "protobuf",
        "owned_by_bazel": True,
    },
    "Stardoc": {
        "git_repository": "https://github.com/bazelbuild/stardoc.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/stardoc/master/.bazelci/presubmit.yml",
        "pipeline_slug": "stardoc",
        "owned_by_bazel": True,
    },
    "Subpar": {
        "git_repository": "https://github.com/google/subpar.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/subpar.yml",
        "pipeline_slug": "subpar",
        "owned_by_bazel": True,
        "disabled_reason": "https://github.com/google/subpar/issues/133",
    },
    "TensorFlow": {
        "git_repository": "https://github.com/tensorflow/tensorflow.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/tensorflow.yml",
        "pipeline_slug": "tensorflow",
    },
    "Tulsi": {
        "git_repository": "https://github.com/bazelbuild/tulsi.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/tulsi/master/.bazelci/presubmit.yml",
        "pipeline_slug": "tulsi-bazel-darwin",
        "disabled_reason": "https://github.com/bazelbuild/tulsi/issues/286",
    },
    "re2": {
        "git_repository": "https://github.com/google/re2.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/re2.yml",
        "pipeline_slug": "re2",
    },
    "rules_android": {
        "git_repository": "https://github.com/bazelbuild/rules_android.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_android/master/.bazelci/postsubmit.yml",
        "pipeline_slug": "rules-android",
        "disabled_reason": "https://github.com/bazelbuild/rules_android/issues/15",
    },
    "rules_android_ndk": {
        "git_repository": "https://github.com/bazelbuild/rules_android_ndk.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_android_ndk/main/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-android-ndk",
    },
    "rules_appengine": {
        "git_repository": "https://github.com/bazelbuild/rules_appengine.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_appengine/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-appengine-appengine",
        "disabled_reason": "https://github.com/bazelbuild/rules_appengine/issues/127",
    },
    "rules_apple": {
        "git_repository": "https://github.com/bazelbuild/rules_apple.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_apple/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-apple-darwin",
    },
    "rules_cc": {
        "git_repository": "https://github.com/bazelbuild/rules_cc.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_cc/main/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-cc",
        "owned_by_bazel": True,
    },
    "rules_closure": {
        "git_repository": "https://github.com/bazelbuild/rules_closure.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_closure/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-closure-closure-compiler",
        "owned_by_bazel": True,
    },
    "rules_docker": {
        "git_repository": "https://github.com/bazelbuild/rules_docker.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_docker/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-docker-docker",
        "disabled_reason": "https://github.com/bazelbuild/rules_docker/issues/1988",
    },
    "rules_dotnet": {
        "git_repository": "https://github.com/bazelbuild/rules_dotnet.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_dotnet/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-dotnet-edge",
    },
    "rules_foreign_cc": {
        "git_repository": "https://github.com/bazelbuild/rules_foreign_cc.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_foreign_cc/main/.bazelci/config.yaml",
        "pipeline_slug": "rules-foreign-cc",
        "owned_by_bazel": True,
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
        "disabled_reason": "https://github.com/bazelbuild/continuous-integration/issues/1202",
    },
    "rules_haskell": {
        "git_repository": "https://github.com/tweag/rules_haskell.git",
        "http_config": "https://raw.githubusercontent.com/tweag/rules_haskell/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-haskell-haskell",
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
        "owned_by_bazel": True,
    },
    "rules_jvm_external - examples": {
        "git_repository": "https://github.com/bazelbuild/rules_jvm_external.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_jvm_external/master/.bazelci/examples.yml",
        "pipeline_slug": "rules-jvm-external-examples",
        "owned_by_bazel": True,
    },
    "rules_k8s": {
        "git_repository": "https://github.com/bazelbuild/rules_k8s.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_k8s/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-k8s-k8s",
        "disabled_reason": "https://github.com/bazelbuild/rules_k8s/issues/668",
    },
    "rules_kotlin": {
        "git_repository": "https://github.com/bazelbuild/rules_kotlin.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_kotlin/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-kotlin-kotlin",
    },
    "rules_nodejs": {
        "git_repository": "https://github.com/bazelbuild/rules_nodejs.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_nodejs/stable/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-nodejs-nodejs",
    },
    "rules_perl": {
        "git_repository": "https://github.com/bazelbuild/rules_perl.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_perl/main/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-perl",
    },
    "rules_proto": {
        "git_repository": "https://github.com/bazelbuild/rules_proto.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_proto/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-proto",
        "owned_by_bazel": True,
    },
    "rules_python": {
        "git_repository": "https://github.com/bazelbuild/rules_python.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_python/main/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-python-python",
        "owned_by_bazel": True,
        "disabled_reason": "waiting on https://github.com/bazelbuild/rules_python/issues/856",
    },
    "rules_rust": {
        "git_repository": "https://github.com/bazelbuild/rules_rust.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_rust/main/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-rust-rustlang",
    },
    "rules_sass": {
        "git_repository": "https://github.com/bazelbuild/rules_sass.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_sass/main/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-sass",
    },
    "rules_scala": {
        "git_repository": "https://github.com/bazelbuild/rules_scala.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_scala/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-scala-scala",
        "disabled_reason": "waiting on https://github.com/bazelbuild/rules_scala/pull/1422",
    },
    "rules_swift": {
        "git_repository": "https://github.com/bazelbuild/rules_swift.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_swift/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-swift-swift",
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

DOCKER_REGISTRY_PREFIX = {
    "bazel-testing": "bazel-public/testing",
    "bazel-trusted": "bazel-public",
    "bazel": "bazel-public",
}[BUILDKITE_ORG]

# A map containing all supported platform names as keys, with the values being
# the platform name in a human readable format, and a the buildkite-agent's
# working directory.
PLATFORMS = {
    "centos7": {
        "name": "CentOS 7 (OpenJDK 8, gcc 4.8.5)",
        "emoji-name": ":centos: 7 (OpenJDK 8, gcc 4.8.5)",
        "downstream-root": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": [],
        "docker-image": f"gcr.io/{DOCKER_REGISTRY_PREFIX}/centos7-java8",
        "python": "python3.6",
    },
    "centos7_java11": {
        "name": "CentOS 7 (OpenJDK 11, gcc 4.8.5)",
        "emoji-name": ":centos: 7 (OpenJDK 11, gcc 4.8.5)",
        "downstream-root": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": [],
        "docker-image": f"gcr.io/{DOCKER_REGISTRY_PREFIX}/centos7-java11",
        "python": "python3.6",
    },
    "centos7_java11_devtoolset10": {
        "name": "CentOS 7 (OpenJDK 11, gcc 10.2.1)",
        "emoji-name": ":centos: 7 (OpenJDK 11, gcc 10.2.1)",
        "downstream-root": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": ["ubuntu1404", "centos7", "linux"],
        "docker-image": f"gcr.io/{DOCKER_REGISTRY_PREFIX}/centos7-java11-devtoolset10",
        "python": "python3.6",
    },
    "debian10": {
        "name": "Debian 10 Buster (OpenJDK 11, gcc 8.3.0)",
        "emoji-name": ":debian: 10 Buster (OpenJDK 11, gcc 8.3.0)",
        "downstream-root": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": [],
        "docker-image": f"gcr.io/{DOCKER_REGISTRY_PREFIX}/debian10-java11",
        "python": "python3.7",
    },
    "debian11": {
        "name": "Debian 11 Bullseye (OpenJDK 17, gcc 10.2.1)",
        "emoji-name": ":debian: 11 Buster (OpenJDK 17, gcc 10.2.1)",
        "downstream-root": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": [],
        "docker-image": f"gcr.io/{DOCKER_REGISTRY_PREFIX}/debian11-java17",
        "python": "python3.9",
    },
    "ubuntu1604": {
        "name": "Ubuntu 16.04 LTS (OpenJDK 8, gcc 5.4.0)",
        "emoji-name": ":ubuntu: 16.04 LTS (OpenJDK 8, gcc 5.4.0)",
        "downstream-root": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": [],
        "docker-image": f"gcr.io/{DOCKER_REGISTRY_PREFIX}/ubuntu1604-java8",
        "python": "python3.6",
    },
    "ubuntu1804": {
        "name": "Ubuntu 18.04 LTS (OpenJDK 11, gcc 7.5.0)",
        "emoji-name": ":ubuntu: 18.04 LTS (OpenJDK 11, gcc 7.5.0)",
        "downstream-root": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": ["ubuntu1804"],
        "docker-image": f"gcr.io/{DOCKER_REGISTRY_PREFIX}/ubuntu1804-java11",
        "python": "python3.6",
    },
    "ubuntu2004": {
        "name": "Ubuntu 20.04 LTS (OpenJDK 11, gcc 9.4.0)",
        "emoji-name": ":ubuntu: 20.04 LTS (OpenJDK 11, gcc 9.4.0)",
        "downstream-root": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": [],
        "docker-image": f"gcr.io/{DOCKER_REGISTRY_PREFIX}/ubuntu2004-java11",
        "python": "python3.8",
    },
    "ubuntu2004_arm64": {
        "name": "Ubuntu 20.04 LTS ARM64 (OpenJDK 11, gcc 9.4.0)",
        "emoji-name": ":ubuntu: 20.04 LTS ARM64 (OpenJDK 11, gcc 9.4.0)",
        "downstream-root": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": [],
        "docker-image": f"gcr.io/{DOCKER_REGISTRY_PREFIX}/ubuntu2004-java11",
        "python": "python3.8",
        "queue": "arm64",
        # TODO: Re-enable always-pull if we also publish docker containers for Linux ARM64
        "always-pull": False,
    },
    "kythe_ubuntu2004": {
        "name": "Kythe (Ubuntu 20.04 LTS, OpenJDK 11, gcc 9.4.0)",
        "emoji-name": "Kythe (:ubuntu: 20.04 LTS, OpenJDK 11, gcc 9.4.0)",
        "downstream-root": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": [],
        "docker-image": f"gcr.io/{DOCKER_REGISTRY_PREFIX}/ubuntu2004-java11-kythe",
        "python": "python3.8",
    },
    "ubuntu2204": {
        "name": "Ubuntu 22.04 (OpenJDK 17, gcc 11.2.0)",
        "emoji-name": ":ubuntu: 22.04 (OpenJDK 17, gcc 11.2.0)",
        "downstream-root": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": [],
        "docker-image": f"gcr.io/{DOCKER_REGISTRY_PREFIX}/ubuntu2204-java17",
        "python": "python3",
    },
    "macos": {
        "name": "macOS (OpenJDK 11, Xcode)",
        "emoji-name": ":darwin: (OpenJDK 11, Xcode)",
        "downstream-root": "/Users/buildkite/builds/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": ["macos"],
        "queue": "macos",
        "python": "python3",
    },
    "macos_arm64": {
        "name": "macOS arm64 (OpenJDK 8, Xcode)",
        "emoji-name": ":darwin: arm64 (OpenJDK 8, Xcode)",
        "downstream-root": "/Users/buildkite/builds/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": ["macos_arm64"],
        "queue": "macos_arm64",
        "python": "python3",
    },
    "windows": {
        "name": "Windows (OpenJDK 11, VS2019)",
        "emoji-name": ":windows: (OpenJDK 11, VS2019)",
        "downstream-root": "c:/b/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": ["windows"],
        "queue": "windows",
        "python": "python.exe",
    },
    "windows_arm64": {
        "name": "Windows ARM64 (OpenJDK 11, VS2019)",
        "emoji-name": ":windows: arm64 (OpenJDK 11, VS2019)",
        "downstream-root": "c:/b/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": ["windows_arm64"],
        # TODO(pcloudy): Switch to windows_arm64 queue when Windows ARM64 machines are available,
        # current we just use x86_64 machines to do cross compile.
        "queue": "windows",
        "python": "python.exe",
    },
    "rbe_ubuntu1604": {
        "name": "RBE (Ubuntu 16.04, OpenJDK 8)",
        "emoji-name": "RBE (:ubuntu: 16.04, OpenJDK 8)",
        "downstream-root": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}/${BUILDKITE_ORGANIZATION_SLUG}-downstream-projects",
        "publish_binary": [],
        "docker-image": f"gcr.io/{DOCKER_REGISTRY_PREFIX}/ubuntu1604-java8",
        "python": "python3.6",
    },
}

BUILDIFIER_DOCKER_IMAGE = "gcr.io/bazel-public/buildifier"

# The platform used for various steps (e.g. stuff that formerly ran on the "pipeline" workers).
DEFAULT_PLATFORM = "ubuntu1804"

# In order to test that "the one Linux binary" that we build for our official releases actually
# works on all Linux distributions that we test on, we use the Linux binary built on our official
# release platform for all Linux downstream tests.
LINUX_BINARY_PLATFORM = "centos7_java11_devtoolset10"

DEFAULT_XCODE_VERSION = "13.0"
XCODE_VERSION_REGEX = re.compile(r"^\d+\.\d+(\.\d+)?$")
XCODE_VERSION_OVERRIDES = {"10.2.1": "10.3", "11.2": "11.2.1", "11.3": "11.3.1"}

BUILD_LABEL_PATTERN = re.compile(r"^Build label: (\S+)$", re.MULTILINE)

BUILDIFIER_STEP_NAME = "Buildifier"

SKIP_TASKS_ENV_VAR = "CI_SKIP_TASKS"

CONFIG_FILE_EXTENSIONS = {".yml", ".yaml"}

KYTHE_DIR = "/usr/local/kythe"

INDEX_UPLOAD_POLICY_ALWAYS = "Always"

INDEX_UPLOAD_POLICY_IF_BUILD_SUCCESS = "IfBuildSuccess"

INDEX_UPLOAD_POLICY_NEVER = "Never"

# The maximum number of tasks allowed in one pipeline yaml config file.
# This is to prevent accidentally creating too many tasks with the martix testing feature.
MAX_TASK_NUMBER = 80


class BuildkiteException(Exception):
    """
    Raised whenever something goes wrong and we should exit with an error.
    """

    pass


class BuildkiteInfraException(Exception):
    """
    Raised whenever something goes wrong with the CI infra and we should immediately exit with an error.
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

    _NEW_BUILD_URL_TEMPLATE = "https://api.buildkite.com/v2/organizations/{}/pipelines/{}/builds"

    _RETRY_JOB_URL_TEMPLATE = (
        "https://api.buildkite.com/v2/organizations/{}/pipelines/{}/builds/{}/jobs/{}/retry"
    )

    _PIPELINE_INFO_URL_TEMPLATE = "https://api.buildkite.com/v2/organizations/{}/pipelines/{}"

    def __init__(self, org, pipeline):
        self._org = org
        self._pipeline = pipeline
        self._token = self._get_buildkite_token()

    def _get_buildkite_token(self):
        return decrypt_token(
            encrypted_token=self._ENCRYPTED_BUILDKITE_API_TESTING_TOKEN
            if THIS_IS_TESTING
            else self._ENCRYPTED_BUILDKITE_API_TOKEN,
            kms_key="buildkite-testing-api-token"
            if THIS_IS_TESTING
            else "buildkite-untrusted-api-token",
        )

    def _open_url(self, url, params=[]):
        try:
            params_str = "".join("&{}={}".format(k, v) for k, v in params)
            return (
                urllib.request.urlopen("{}?access_token={}{}".format(url, self._token, params_str))
                .read()
                .decode("utf-8", "ignore")
            )
        except urllib.error.HTTPError as ex:
            raise BuildkiteException("Failed to open {}: {} - {}".format(url, ex.code, ex.reason))

    def get_pipeline_info(self):
        """Get details for a pipeline given its organization slug
        and pipeline slug.
        See https://buildkite.com/docs/apis/rest-api/pipelines#get-a-pipeline

        Returns
        -------
        dict
            the metadata for the pipeline
        """
        url = self._PIPELINE_INFO_URL_TEMPLATE.format(self._org, self._pipeline)
        output = self._open_url(url)
        return json.loads(output)

    def get_build_info(self, build_number):
        """Get build info for a pipeline with a given build number
        See https://buildkite.com/docs/apis/rest-api/builds#get-a-build

        Parameters
        ----------
        build_number : the build number

        Returns
        -------
        dict
            the metadata for the build
        """
        url = self._BUILD_STATUS_URL_TEMPLATE.format(self._org, self._pipeline, build_number)
        output = self._open_url(url)
        return json.loads(output)

    def get_build_info_list(self, params):
        """Get a list of build infos for this pipeline
        See https://buildkite.com/docs/apis/rest-api/builds#list-builds-for-a-pipeline

        Parameters
        ----------
        params : the parameters to filter the result

        Returns
        -------
        list of dict
            the metadata for a list of builds
        """
        url = self._BUILD_STATUS_URL_TEMPLATE.format(self._org, self._pipeline, "")
        output = self._open_url(url, params)
        return json.loads(output)

    def get_build_log(self, job):
        return self._open_url(job["raw_log_url"])

    @staticmethod
    def _check_response(response, expected_status_code):
        if response.status_code != expected_status_code:
            eprint("Exit code:", response.status_code)
            eprint("Response:\n", response.text)
            response.raise_for_status()

    def trigger_new_build(self, commit, message=None, env={}):
        """Trigger a new build at a given commit and return the build metadata.
        See https://buildkite.com/docs/apis/rest-api/builds#create-a-build

        Parameters
        ----------
        commit : the commit we want to build at
        message : the message we should as the build titile
        env : (optional) the environment variables to set

        Returns
        -------
        dict
            the metadata for the build
        """
        pipeline_info = self.get_pipeline_info()
        if not pipeline_info:
            raise BuildkiteException(f"Cannot find pipeline info for pipeline {self._pipeline}.")

        url = self._NEW_BUILD_URL_TEMPLATE.format(self._org, self._pipeline)
        data = {
            "commit": commit,
            "branch": pipeline_info.get("default_branch") or "master",
            "message": message if message else f"Trigger build at {commit}",
            "env": env,
            "ignore_pipeline_branch_filters": "true",
        }
        response = requests.post(url + "?access_token=" + self._token, json=data)
        BuildkiteClient._check_response(response, requests.codes.created)
        return json.loads(response.text)

    def trigger_job_retry(self, build_number, job_id):
        """Trigger a job retry and return the job metadata.
        See https://buildkite.com/docs/apis/rest-api/jobs#retry-a-job

        Parameters
        ----------
        build_number : the number of the build we want to retry
        job_id : the id of the job we want to retry

        Returns
        -------
        dict
            the metadata for the job
        """
        url = self._RETRY_JOB_URL_TEMPLATE.format(self._org, self._pipeline, build_number, job_id)
        response = requests.put(url + "?access_token=" + self._token)
        BuildkiteClient._check_response(response, requests.codes.ok)
        return json.loads(response.text)

    def wait_job_to_finish(self, build_number, job_id, interval_time=30, logger=None):
        """Wait a job to finish and return the job metadata

        Parameters
        ----------
        build_number : the number of the build we want to wait
        job_id : the id of the job we want to wait
        interval_time : (optional) the interval time to check the build status, default to 30s
        logger : (optional) a logger to report progress

        Returns
        -------
        dict
            the latest metadata for the job
        """
        t = 0
        build_info = self.get_build_info(build_number)
        while True:
            for job in build_info["jobs"]:
                if job["id"] == job_id:
                    state = job["state"]
                    if state != "scheduled" and state != "running" and state != "assigned":
                        return job
                    break
            else:
                raise BuildkiteException(
                    f"job id {job_id} doesn't exist in build " + build_info["web_url"]
                )
            url = build_info["web_url"]
            if logger:
                logger.log(f"Waiting for {url}, waited {t} seconds...")
            time.sleep(interval_time)
            t += interval_time
            build_info = self.get_build_info(build_number)

    def wait_build_to_finish(self, build_number, interval_time=30, logger=None):
        """Wait a build to finish and return the build metadata

        Parameters
        ----------
        build_number : the number of the build we want to wait
        interval_time : (optional) the interval time to check the build status, default to 30s
        logger : (optional) a logger to report progress

        Returns
        -------
        dict
            the latest metadata for the build
        """
        t = 0
        build_info = self.get_build_info(build_number)
        while build_info["state"] == "scheduled" or build_info["state"] == "running":
            url = build_info["web_url"]
            if logger:
                logger.log(f"Waiting for {url}, waited {t} seconds...")
            time.sleep(interval_time)
            t += interval_time
            build_info = self.get_build_info(build_number)
        return build_info


def decrypt_token(encrypted_token, kms_key):
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
                kms_key,
                "--ciphertext-file",
                "-",
                "--plaintext-file",
                "-",
            ],
            input=base64.b64decode(encrypted_token),
            env=os.environ,
        )
        .decode("utf-8")
        .strip()
    )


def eprint(*args, **kwargs):
    """
    Print to stderr and flush (just in case).
    """
    print(*args, flush=True, file=sys.stderr, **kwargs)


def is_windows():
    return os.name == "nt"


def is_mac():
    return platform_module.system() == "Darwin"


def gsutil_command():
    return "gsutil.cmd" if is_windows() else "gsutil"


def gcloud_command():
    return "gcloud.cmd" if is_windows() else "gcloud"


def downstream_projects_root(platform):
    downstream_root = os.path.expandvars(PLATFORMS[platform]["downstream-root"])
    if platform == "windows" and os.path.exists("d:/b"):
        # If this is a Windows machine with a local SSD, the build directory is
        # on drive D.
        downstream_root = downstream_root.replace("c:/b/", "d:/b/")
    if not os.path.exists(downstream_root):
        os.makedirs(downstream_root)
    return downstream_root


def match_matrix_attr_pattern(s):
    return re.match("^\${{\s*(\w+)\s*}}$", s)


def get_matrix_attributes(task):
    """Get unexpanded matrix attributes from the given task.

    If a value of field matches "${{<name>}}", then <name> is a wanted matrix attribute.
    eg. platform: ${{ platform }}
    """
    attributes = []
    for key, value in task.items():
        if type(value) is str:
            res = match_matrix_attr_pattern(value)
            if res:
                attributes.append(res.groups()[0])
    return list(set(attributes))


def get_combinations(matrix, attributes):
    """Given a matrix and the wanted attributes, return all possible combinations.

    eg.
    With matrix = {'a': [1, 2], 'b': [1], 'c': [1]},
    if attributes = ['a', 'b'], then returns [[('a', 1), ('b', 1)], [('a', 2), ('b', 1)]]
    if attributes = ['b', 'c'], then returns [[('b', 1), ('c', 1)]]
    if attributes = ['c'], then returns [[('c', 1)]]
    """
    for attr in attributes:
        if attr not in matrix:
            raise BuildkiteException("${{ %s }} is not defined in `matrix` section." % attr)
    pairs = [[(attr, value) for value in matrix[attr]] for attr in attributes]
    return itertools.product(*pairs)


def get_expanded_task(task, combination):
    """Expand a task with the given combination of values of attributes."""
    combination = dict(combination)
    expanded_task = copy.deepcopy(task)
    for key, value in task.items():
        if type(value) is str:
            res = match_matrix_attr_pattern(value)
            if res:
                attr = res.groups()[0]
                expanded_task[key] = combination[attr]
    return expanded_task


def fetch_configs(http_url, file_config):
    """
    If specified fetches the build configuration from file_config or http_url, else tries to
    read it from .bazelci/presubmit.yml.
    Returns the json configuration as a python data structure.
    """
    if file_config is not None and http_url is not None:
        raise BuildkiteException("file_config and http_url cannot be set at the same time")

    return load_config(http_url, file_config)


def expand_task_config(config):
    # Expand tasks that uses attributes defined in the matrix section.
    # The original task definition expands to multiple tasks for each possible combination.
    tasks_to_expand = []
    expanded_tasks = {}
    matrix = config.pop("matrix", {})
    for key, value in matrix.items():
        if type(key) is not str or type(value) is not list:
            raise BuildkiteException("Expect `matrix` is a map of str -> list")

    for task in config["tasks"]:
        attributes = get_matrix_attributes(config["tasks"][task])
        if attributes:
            tasks_to_expand.append(task)
            count = 1
            for combination in get_combinations(matrix, attributes):
                expanded_task_name = "%s_config_%.2d" % (task, count)
                count += 1
                expanded_tasks[expanded_task_name] = get_expanded_task(
                    config["tasks"][task], combination
                )

    for task in tasks_to_expand:
        config["tasks"].pop(task)
    config["tasks"].update(expanded_tasks)


def load_config(http_url, file_config, allow_imports=True):
    if http_url:
        config = load_remote_yaml_file(http_url)
    else:
        file_config = file_config or ".bazelci/presubmit.yml"
        with open(file_config, "r") as fd:
            config = yaml.safe_load(fd)

    # Legacy mode means that there is exactly one task per platform (e.g. ubuntu1604_nojdk),
    # which means that we can get away with using the platform name as task ID.
    # No other updates are needed since get_platform_for_task() falls back to using the
    # task ID as platform if there is no explicit "platforms" field.
    if "platforms" in config:
        config["tasks"] = config.pop("platforms")

    if "tasks" not in config:
        config["tasks"] = {}

    expand_task_config(config)

    imports = config.pop("imports", None)
    if imports:
        if not allow_imports:
            raise BuildkiteException("Nested imports are not allowed")

        for i in imports:
            imported_tasks = load_imported_tasks(i, http_url, file_config)
            config["tasks"].update(imported_tasks)

    if len(config["tasks"]) > MAX_TASK_NUMBER:
        raise BuildkiteException(
            "The number of tasks in one config file is limited to %s!" % MAX_TASK_NUMBER
        )

    return config


def load_remote_yaml_file(http_url):
    with urllib.request.urlopen(http_url) as resp:
        reader = codecs.getreader("utf-8")
        return yaml.safe_load(reader(resp))


def load_imported_tasks(import_name, http_url, file_config):
    if "/" in import_name:
        raise BuildkiteException("Invalid import '%s'" % import_name)

    old_path = http_url or file_config
    new_path = "%s%s" % (old_path[: old_path.rfind("/") + 1], import_name)
    if http_url:
        http_url = new_path
    else:
        file_config = new_path

    imported_config = load_config(http_url=http_url, file_config=file_config, allow_imports=False)

    namespace = import_name.partition(".")[0]
    tasks = {}
    for task_name, task_config in imported_config["tasks"].items():
        fix_imported_task_platform(task_name, task_config)
        fix_imported_task_name(namespace, task_config)
        fix_imported_task_working_directory(namespace, task_config)
        tasks["%s_%s" % (namespace, task_name)] = task_config

    return tasks


def fix_imported_task_platform(task_name, task_config):
    if "platform" not in task_config:
        task_config["platform"] = task_name


def fix_imported_task_name(namespace, task_config):
    old_name = task_config.get("name")
    task_config["name"] = "%s (%s)" % (namespace, old_name) if old_name else namespace


def fix_imported_task_working_directory(namespace, task_config):
    old_dir = task_config.get("working_directory")
    task_config["working_directory"] = os.path.join(namespace, old_dir) if old_dir else namespace


def print_collapsed_group(name):
    eprint("\n\n--- {0}\n\n".format(name))


def print_expanded_group(name):
    eprint("\n\n+++ {0}\n\n".format(name))


def is_trueish(s):
    return str(s).lower() in ["true", "1", "t", "y", "yes"]


def use_bazelisk_migrate():
    """
    If USE_BAZELISK_MIGRATE is set, we use `bazelisk --migrate` to test incompatible flags.
    """
    return is_trueish(os.environ.get("USE_BAZELISK_MIGRATE"))


def bazelisk_flags():
    return ["--migrate"] if use_bazelisk_migrate() else []


def calculate_flags(task_config, task_config_key, action_key, tmpdir, test_env_vars):
    include_json_profile = task_config.get("include_json_profile", [])
    capture_corrupted_outputs = task_config.get("capture_corrupted_outputs", [])

    json_profile_flags = []
    json_profile_out = None
    if action_key in include_json_profile:
        json_profile_out = os.path.join(tmpdir, "{}.profile.gz".format(action_key))
        json_profile_flags = ["--profile={}".format(json_profile_out)]

    capture_corrupted_outputs_flags = []
    capture_corrupted_outputs_dir = None
    if action_key in capture_corrupted_outputs:
        capture_corrupted_outputs_dir = os.path.join(
            tmpdir, "{}_corrupted_outputs".format(action_key)
        )
        capture_corrupted_outputs_flags = [
            "--experimental_remote_capture_corrupted_outputs={}".format(
                capture_corrupted_outputs_dir
            )
        ]

    flags = task_config.get(task_config_key) or []
    flags += json_profile_flags
    flags += capture_corrupted_outputs_flags
    # We have to add --test_env flags to `build`, too, otherwise Bazel
    # discards its analysis cache between `build` and `test`.
    if test_env_vars:
        flags += ["--test_env={}".format(v) for v in test_env_vars]

    return flags, json_profile_out, capture_corrupted_outputs_dir


def execute_commands(
    task_config,
    platform,
    git_repository,
    git_commit,
    repo_location,
    use_bazel_at_commit,
    use_but,
    save_but,
    needs_clean,
    build_only,
    test_only,
    monitor_flaky_tests,
    bazel_version=None,
):
    if use_bazelisk_migrate():
        # If we are testing incompatible flags with Bazelisk,
        # use Bazel@last_green if USE_BAZEL_VERSION env var is not set explicitly.
        if "USE_BAZEL_VERSION" not in os.environ:
            bazel_version = "last_green"

        # Override use_but in case we are in the downstream pipeline so that it doesn't try to
        # download Bazel built from previous jobs.
        use_but = False

        # Set BAZELISK_INCOMPATIBLE_FLAGS to tell Bazelisk which flags to test.
        os.environ["BAZELISK_INCOMPATIBLE_FLAGS"] = ",".join(fetch_incompatible_flags().keys())

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
        if is_mac():
            activate_xcode(task_config)

        # If the CI worker runs Bazelisk, we need to forward all required env variables to the test.
        # Otherwise any integration test that invokes Bazel (=Bazelisk in this case) will fail.
        test_env_vars = ["LocalAppData"] if platform == "windows" else ["HOME"]

        # CI should have its own user agent so that we can remove it from Bazel download statistics.
        os.environ["BAZELISK_USER_AGENT"] = "Bazelisk/BazelCI"
        test_env_vars.append("BAZELISK_USER_AGENT")

        if repo_location:
            os.chdir(repo_location)
        elif git_repository:
            clone_git_repository(git_repository, platform, git_commit)

        # We use one binary for all Linux platforms (because we also just release one binary for all
        # Linux versions and we have to ensure that it works on all of them).
        binary_platform = platform if is_mac() or is_windows() else LINUX_BINARY_PLATFORM

        bazel_binary = "bazel"
        if use_bazel_at_commit:
            print_collapsed_group(":gcloud: Downloading Bazel built at " + use_bazel_at_commit)
            # Linux binaries are published under platform name "centos7"
            if binary_platform == LINUX_BINARY_PLATFORM:
                binary_platform = "centos7"
            os.environ["USE_BAZEL_VERSION"] = download_bazel_binary_at_commit(
                tmpdir, binary_platform, use_bazel_at_commit
            )
            print_collapsed_group(":bazel: Using Bazel at " + os.environ["USE_BAZEL_VERSION"])
        elif use_but:
            print_collapsed_group(":gcloud: Downloading Bazel Under Test")
            os.environ["USE_BAZEL_VERSION"] = download_bazel_binary(tmpdir, binary_platform)
            print_collapsed_group(":bazel: Using Bazel at " + os.environ["USE_BAZEL_VERSION"])
        else:
            print_collapsed_group(":bazel: Using Bazel version " + bazel_version)
            if bazel_version:
                os.environ["USE_BAZEL_VERSION"] = bazel_version
        if "USE_BAZEL_VERSION" in os.environ and not task_config.get(
            "skip_use_bazel_version_for_test", False
        ):
            # This will only work if the bazel binary in $PATH is actually a bazelisk binary
            # (https://github.com/bazelbuild/bazelisk).
            test_env_vars.append("USE_BAZEL_VERSION")

        for key, value in task_config.get("environment", {}).items():
            # We have to explicitly convert the value to a string, because sometimes YAML tries to
            # be smart and converts strings like "true" and "false" to booleans.
            os.environ[key] = os.path.expandvars(str(value))

        # Set BAZELISK_SHUTDOWN to 1 when we use bazelisk --migrate on Windows.
        # This is a workaround for https://github.com/bazelbuild/continuous-integration/issues/1012
        if use_bazelisk_migrate() and platform == "windows":
            os.environ["BAZELISK_SHUTDOWN"] = "1"

        cmd_exec_func = execute_batch_commands if platform == "windows" else execute_shell_commands
        cmd_exec_func(task_config.get("setup", None))

        # Allow the config to override the current working directory.
        required_prefix = os.getcwd()
        requested_working_dir = os.path.abspath(task_config.get("working_directory", ""))
        if os.path.commonpath([required_prefix, requested_working_dir]) != required_prefix:
            raise BuildkiteException("working_directory refers to a path outside the workspace")
        os.chdir(requested_working_dir)

        # Set OUTPUT_BASE environment variable
        os.environ["OUTPUT_BASE"] = get_output_base(bazel_binary, platform)

        if platform == "windows":
            execute_batch_commands(task_config.get("batch_commands", None))
        else:
            execute_shell_commands(task_config.get("shell_commands", None))

        bazel_version = print_bazel_version_info(bazel_binary, platform)

        print_environment_variables_info()

        execute_bazel_run(bazel_binary, platform, task_config.get("run_targets", None))

        if needs_clean:
            execute_bazel_clean(bazel_binary, platform)

        build_targets, test_targets, coverage_targets, index_targets = calculate_targets(
            task_config, platform, bazel_binary, build_only, test_only
        )

        if build_targets:
            (
                build_flags,
                json_profile_out_build,
                capture_corrupted_outputs_dir_build,
            ) = calculate_flags(task_config, "build_flags", "build", tmpdir, test_env_vars)
            try:
                release_name = get_release_name_from_branch_name()
                execute_bazel_build(
                    bazel_version,
                    bazel_binary,
                    platform,
                    build_flags
                    + (
                        ["--stamp", "--embed_label=%s" % release_name]
                        if save_but and release_name
                        else []
                    ),
                    build_targets,
                    None,
                )
                if save_but:
                    upload_bazel_binary(platform)
            finally:
                if json_profile_out_build:
                    upload_json_profile(json_profile_out_build, tmpdir)
                if capture_corrupted_outputs_dir_build:
                    upload_corrupted_outputs(capture_corrupted_outputs_dir_build, tmpdir)

        if test_targets:
            test_flags, json_profile_out_test, capture_corrupted_outputs_dir_test = calculate_flags(
                task_config, "test_flags", "test", tmpdir, test_env_vars
            )
            if not is_windows():
                # On platforms that support sandboxing (Linux, MacOS) we have
                # to allow access to Bazelisk's cache directory.
                # However, the flag requires the directory to exist,
                # so we create it here in order to not crash when a test
                # does not invoke Bazelisk.
                bazelisk_cache_dir = get_bazelisk_cache_directory()
                os.makedirs(bazelisk_cache_dir, mode=0o755, exist_ok=True)
                test_flags.append("--sandbox_writable_path={}".format(bazelisk_cache_dir))

            test_bep_file = os.path.join(tmpdir, "test_bep.json")
            upload_thread = threading.Thread(
                target=upload_test_logs_from_bep,
                args=(test_bep_file, tmpdir, monitor_flaky_tests),
            )
            try:
                upload_thread.start()
                try:
                    execute_bazel_test(
                        bazel_version,
                        bazel_binary,
                        platform,
                        test_flags,
                        test_targets,
                        test_bep_file,
                        monitor_flaky_tests,
                    )
                finally:
                    if json_profile_out_test:
                        upload_json_profile(json_profile_out_test, tmpdir)
                    if capture_corrupted_outputs_dir_test:
                        upload_corrupted_outputs(capture_corrupted_outputs_dir_test, tmpdir)
            finally:
                upload_thread.join()

        if coverage_targets:
            (
                coverage_flags,
                json_profile_out_coverage,
                capture_corrupted_outputs_dir_coverage,
            ) = calculate_flags(task_config, "coverage_flags", "coverage", tmpdir, test_env_vars)
            try:
                execute_bazel_coverage(
                    bazel_version,
                    bazel_binary,
                    platform,
                    coverage_flags,
                    coverage_targets,
                )
            finally:
                if json_profile_out_coverage:
                    upload_json_profile(json_profile_out_coverage, tmpdir)
                if capture_corrupted_outputs_dir_coverage:
                    upload_corrupted_outputs(capture_corrupted_outputs_dir_coverage, tmpdir)

        if index_targets:
            (
                index_flags,
                json_profile_out_index,
                capture_corrupted_outputs_dir_index,
            ) = calculate_flags(task_config, "index_flags", "index", tmpdir, test_env_vars)
            index_upload_policy = task_config.get("index_upload_policy", "IfBuildSuccess")
            index_upload_gcs = task_config.get("index_upload_gcs", False)

            try:
                should_upload_kzip = (
                    True if index_upload_policy == INDEX_UPLOAD_POLICY_ALWAYS else False
                )
                try:
                    execute_bazel_build_with_kythe(
                        bazel_version,
                        bazel_binary,
                        platform,
                        index_flags,
                        index_targets,
                        None,
                    )

                    if index_upload_policy == INDEX_UPLOAD_POLICY_IF_BUILD_SUCCESS:
                        should_upload_kzip = True
                except subprocess.CalledProcessError as e:
                    # If not running with Always policy, raise the build error.
                    if index_upload_policy != INDEX_UPLOAD_POLICY_ALWAYS:
                        handle_bazel_failure(e, "build")

                if should_upload_kzip and not is_pull_request():
                    try:
                        merge_and_upload_kythe_kzip(platform, index_upload_gcs)
                    except subprocess.CalledProcessError:
                        raise BuildkiteException("Failed to upload kythe kzip")
            finally:
                if json_profile_out_index:
                    upload_json_profile(json_profile_out_index, tmpdir)
                if capture_corrupted_outputs_dir_index:
                    upload_corrupted_outputs(capture_corrupted_outputs_dir_index, tmpdir)

    finally:
        terminate_background_process(sc_process)
        if tmpdir:
            shutil.rmtree(tmpdir)


def activate_xcode(task_config):
    # Get the Xcode version from the config.
    wanted_xcode_version = task_config.get("xcode_version", DEFAULT_XCODE_VERSION)
    print_collapsed_group(":xcode: Activating Xcode {}...".format(wanted_xcode_version))

    # Ensure it's a valid version number.
    if not isinstance(wanted_xcode_version, str):
        raise BuildkiteException(
            "Version number '{}' is not a string. Did you forget to put it in quotes?".format(
                wanted_xcode_version
            )
        )
    if not XCODE_VERSION_REGEX.match(wanted_xcode_version):
        raise BuildkiteException(
            "Invalid Xcode version format '{}', must match the format X.Y[.Z].".format(
                wanted_xcode_version
            )
        )

    # This is used to replace e.g. 11.2 with 11.2.1 without having to update all configs.
    xcode_version = XCODE_VERSION_OVERRIDES.get(wanted_xcode_version, wanted_xcode_version)

    # This falls back to a default version if the selected version is not available.
    supported_versions = sorted(
        # Stripping "Xcode" prefix and ".app" suffix from e.g. "Xcode12.0.1.app" leaves just the version number.
        [os.path.basename(x)[5:-4] for x in glob("/Applications/Xcode*.app")],
        reverse=True,
    )
    if xcode_version not in supported_versions:
        xcode_version = DEFAULT_XCODE_VERSION
    if xcode_version != wanted_xcode_version:
        print_collapsed_group(
            ":xcode: Fixed Xcode version: {} -> {}...".format(wanted_xcode_version, xcode_version)
        )
        lines = [
            "Your selected Xcode version {} was not available on the machine.".format(
                wanted_xcode_version
            ),
            "Bazel CI automatically picked a fallback version: {}.".format(xcode_version),
            "Available versions are: {}.".format(supported_versions),
        ]
        execute_command(
            [
                "buildkite-agent",
                "annotate",
                "--style=warning",
                "\n".join(lines),
                "--context",
                "ctx-xcode_version_fixed",
            ]
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


def get_bazelisk_cache_directory():
    # The path relies on the behavior of Go's os.UserCacheDir()
    # and of the Go version of Bazelisk.
    cache_dir = "Library/Caches" if is_mac() else ".cache"
    return os.path.join(os.environ.get("HOME"), cache_dir, "bazelisk")


def current_branch_is_main_branch():
    return os.getenv("BUILDKITE_BRANCH") in ("master", "stable", "main", "google")


def get_release_name_from_branch_name():
    # TODO(pcloudy): Find a better way to do this
    if os.getenv("BUILDKITE_PIPELINE_SLUG") == "publish-bazel-binaries":
        return None
    res = re.match(r"release-(\d+\.\d+\.\d+(rc\d+)?).*", os.getenv("BUILDKITE_BRANCH"))
    return res.group(1) if res else None


def is_pull_request():
    third_party_repo = os.getenv("BUILDKITE_PULL_REQUEST_REPO", "")
    return len(third_party_repo) > 0


def print_bazel_version_info(bazel_binary, platform):
    print_collapsed_group(":information_source: Bazel Info")
    version_output = execute_command_and_get_output(
        [bazel_binary] + common_startup_flags() + ["--nosystem_rc", "--nohome_rc", "version"]
    )
    execute_command(
        [bazel_binary] + common_startup_flags() + ["--nosystem_rc", "--nohome_rc", "info"]
    )

    match = BUILD_LABEL_PATTERN.search(version_output)
    return match.group(1) if match else "unreleased binary"


def print_environment_variables_info():
    print_collapsed_group(":information_source: Environment Variables")
    for key, value in os.environ.items():
        eprint("%s=(%s)" % (key, value))


def upload_bazel_binary(platform):
    print_collapsed_group(":gcloud: Uploading Bazel Under Test")
    if platform == "windows":
        binary_dir = r"bazel-bin\src"
        binary_name = r"bazel.exe"
        binary_nojdk_name = r"bazel_nojdk.exe"
    else:
        binary_dir = "bazel-bin/src"
        binary_name = "bazel"
        binary_nojdk_name = "bazel_nojdk"
    execute_command(["buildkite-agent", "artifact", "upload", binary_name], cwd=binary_dir)
    execute_command(["buildkite-agent", "artifact", "upload", binary_nojdk_name], cwd=binary_dir)


def merge_and_upload_kythe_kzip(platform, index_upload_gcs):
    print_collapsed_group(":gcloud: Uploading kythe kzip")

    kzips = glob("bazel-out/*/extra_actions/**/*.kzip", recursive=True)

    build_number = os.getenv("BUILDKITE_BUILD_NUMBER")
    git_commit = os.getenv("BUILDKITE_COMMIT")
    final_kzip_name = "{}-{}-{}.kzip".format(build_number, platform, git_commit)

    execute_command([f"{KYTHE_DIR}/tools/kzip", "merge", "--output", final_kzip_name] + kzips)
    execute_command(["buildkite-agent", "artifact", "upload", final_kzip_name])

    if index_upload_gcs:
        pipeline = os.getenv("BUILDKITE_PIPELINE_SLUG")
        branch = os.getenv("BUILDKITE_BRANCH")
        destination = KZIPS_BUCKET + pipeline + "/" + branch + "/" + final_kzip_name
        print("Uploading to GCS {}".format(destination))
        execute_command([gsutil_command(), "cp", final_kzip_name, destination])


def download_binary(dest_dir, platform, binary_name):
    source_step = create_label(platform, "Bazel", build_only=True)
    execute_command(
        ["buildkite-agent", "artifact", "download", binary_name, dest_dir, "--step", source_step]
    )
    bazel_binary_path = os.path.join(dest_dir, binary_name)
    st = os.stat(bazel_binary_path)
    os.chmod(bazel_binary_path, st.st_mode | stat.S_IEXEC)
    return bazel_binary_path


def download_bazel_binary(dest_dir, platform):
    binary_name = "bazel.exe" if platform == "windows" else "bazel"
    return download_binary(dest_dir, platform, binary_name)


def download_bazel_nojdk_binary(dest_dir, platform):
    binary_name = "bazel_nojdk.exe" if platform == "windows" else "bazel_nojdk"
    return download_binary(dest_dir, platform, binary_name)


def download_binary_at_commit(bazel_git_commit, bazel_binary_url, bazel_binary_path):
    try:
        execute_command([gsutil_command(), "cp", bazel_binary_url, bazel_binary_path])
    except subprocess.CalledProcessError as e:
        raise BuildkiteInfraException(
            "Failed to download Bazel binary at %s, error message:\n%s" % (bazel_git_commit, str(e))
        )
    st = os.stat(bazel_binary_path)
    os.chmod(bazel_binary_path, st.st_mode | stat.S_IEXEC)
    return bazel_binary_path


def download_bazel_binary_at_commit(dest_dir, platform, bazel_git_commit):
    url = bazelci_builds_gs_url(platform, bazel_git_commit)
    path = os.path.join(dest_dir, "bazel.exe" if platform == "windows" else "bazel")
    return download_binary_at_commit(bazel_git_commit, url, path)


def download_bazel_nojdk_binary_at_commit(dest_dir, platform, bazel_git_commit):
    url = bazelci_builds_nojdk_gs_url(platform, bazel_git_commit)
    path = os.path.join(dest_dir, "bazel_nojdk.exe" if platform == "windows" else "bazel_nojdk")
    return download_binary_at_commit(bazel_git_commit, url, path)


def download_bazelci_agent(dest_dir, version):
    postfix = ""
    if is_windows():
        postfix = "x86_64-pc-windows-msvc.exe"
    elif is_mac():
        if platform_module.machine() == "arm64":
            postfix = "aarch64-apple-darwin"
        else:
            postfix = "x86_64-apple-darwin"
    else:
        postfix = "x86_64-unknown-linux-musl"

    name = "bazelci-agent-{}-{}".format(version, postfix)
    url = (
        "https://github.com/bazelbuild/continuous-integration/releases/download/agent-{}/{}".format(
            version, name
        )
    )
    path = os.path.join(dest_dir, "bazelci-agent.exe" if is_windows() else "bazelci-agent")
    execute_command(["curl", "-sSL", url, "-o", path])
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)
    return path


def get_mirror_root():
    if is_mac():
        return "/usr/local/var/bazelbuild/"
    elif is_windows():
        return "c:\\buildkite\\bazelbuild\\"

    return "/var/lib/bazelbuild/"


def clone_git_repository(git_repository, platform, git_commit=None):
    root = downstream_projects_root(platform)
    project_name = re.search(r"/([^/]+)\.git$", git_repository).group(1)
    clone_path = os.path.join(root, project_name)
    print_collapsed_group(
        "Fetching %s sources at %s" % (project_name, git_commit if git_commit else "HEAD")
    )

    mirror_path = get_mirror_root() + re.sub(r"[^0-9A-Za-z]", "-", git_repository)

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
    execute_command(["git", "submodule", "foreach", "--recursive", "git clean -fdqx"])
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
    execute_command(["git", "submodule", "foreach", "--recursive", "git reset --hard"])
    execute_command(["git", "clean", "-fdqx"])
    execute_command(["git", "submodule", "foreach", "--recursive", "git clean -fdqx"])
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
    shell_command = "\n".join(["set -e"] + commands)
    execute_command([shell_command], shell=True)


def handle_bazel_failure(exception, action):
    msg = "bazel {0} failed with exit code {1}".format(action, exception.returncode)
    if use_bazelisk_migrate():
        print_collapsed_group(msg)
    else:
        raise BuildkiteException(msg)


def execute_bazel_run(bazel_binary, platform, targets):
    if not targets:
        return
    print_collapsed_group("Setup (Run Targets)")
    for target in targets:
        try:
            execute_command(
                [bazel_binary]
                + bazelisk_flags()
                + common_startup_flags()
                + ["run"]
                + common_build_flags(None, platform)
                + [target]
            )
        except subprocess.CalledProcessError as e:
            handle_bazel_failure(e, "run")


def remote_caching_flags(platform, accept_cached=True):
    # Only enable caching for untrusted and testing builds.
    if CLOUD_PROJECT not in ["bazel-untrusted"]:
        return []

    platform_cache_key = [BUILDKITE_ORG.encode("utf-8")]
    # Whenever the remote cache was known to have been poisoned increase the number below
    platform_cache_key += ["cache-poisoning-20220912".encode("utf-8")]

    # We don't enable remote caching on the Linux ARM64 machine since it doesn't have access to GCS.
    if platform == "ubuntu2004_arm64":
        return []

    if is_mac():
        platform_cache_key += [
            # macOS version:
            subprocess.check_output(["/usr/bin/sw_vers", "-productVersion"]),
            # Path to Xcode:
            subprocess.check_output(["/usr/bin/xcode-select", "-p"]),
            # Xcode version:
            subprocess.check_output(["/usr/bin/xcodebuild", "-version"]),
        ]
        # Use a local cache server for our macOS machines.
        flags = ["--remote_cache=http://100.107.73.148"]
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

    if not accept_cached:
        flags += ["--noremote_accept_cached"]

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
    elif is_windows():
        return "8"
    elif is_mac() and THIS_IS_TESTING:
        return "4"
    elif is_mac():
        return "8"
    return "12"


def common_startup_flags():
    if is_windows():
        if os.path.exists("D:/b"):
            # This machine has a local SSD mounted as drive D.
            return ["--output_user_root=D:/b"]
        else:
            # This machine uses its PD-SSD as the build directory.
            return ["--output_user_root=C:/b"]
    return []


def common_build_flags(bep_file, platform):
    flags = [
        "--show_progress_rate_limit=5",
        "--curses=yes",
        "--color=yes",
        "--terminal_columns=143",
        "--show_timestamps",
        "--verbose_failures",
        "--jobs=" + concurrent_jobs(platform),
        "--announce_rc",
        "--experimental_repository_cache_hardlinks",
        # Some projects set --disk_cache in their project-specific bazelrc, which we never want on
        # CI, so let's just disable it explicitly.
        "--disk_cache=",
    ]

    if is_windows():
        pass
    elif is_mac():
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
        "--incompatible_strict_action_env",
        "--google_default_credentials",
        "--toolchain_resolution_debug",
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


def get_output_base(bazel_binary, platform):
    return execute_command_and_get_output(
        [bazel_binary] + common_startup_flags() + ["info", "output_base"],
        print_output=False,
    ).strip()


def compute_flags(platform, flags, bep_file, bazel_binary, enable_remote_cache=False):
    aggregated_flags = common_build_flags(bep_file, platform)
    if not remote_enabled(flags):
        if platform.startswith("rbe_"):
            aggregated_flags += rbe_flags(flags, accept_cached=enable_remote_cache)
        else:
            aggregated_flags += remote_caching_flags(platform, accept_cached=enable_remote_cache)
    aggregated_flags += flags

    for i, flag in enumerate(aggregated_flags):
        if "$HOME" in flag:
            if is_windows():
                if os.path.exists("D:/"):
                    home = "D:"
                else:
                    home = "C:/b"
            elif is_mac():
                home = "/Users/buildkite"
            else:
                home = "/var/lib/buildkite-agent"
            aggregated_flags[i] = flag.replace("$HOME", home)
        if "$OUTPUT_BASE" in flag:
            output_base = get_output_base(bazel_binary, platform)
            aggregated_flags[i] = flag.replace("$OUTPUT_BASE", output_base)

    return aggregated_flags


def execute_bazel_clean(bazel_binary, platform):
    print_expanded_group(":bazel: Clean")

    try:
        execute_command([bazel_binary] + common_startup_flags() + ["clean", "--expunge"])
    except subprocess.CalledProcessError as e:
        raise BuildkiteException("bazel clean failed with exit code {}".format(e.returncode))


def kythe_startup_flags():
    return [f"--bazelrc={KYTHE_DIR}/extractors.bazelrc"]


def kythe_build_flags():
    return [
        "--experimental_convenience_symlinks=normal",
        f"--override_repository=kythe_release={KYTHE_DIR}",
    ]


def execute_bazel_build(bazel_version, bazel_binary, platform, flags, targets, bep_file):
    print_collapsed_group(":bazel: Computing flags for build step")
    aggregated_flags = compute_flags(
        platform,
        flags,
        bep_file,
        bazel_binary,
        enable_remote_cache=True,
    )

    print_expanded_group(":bazel: Build ({})".format(bazel_version))
    try:
        execute_command(
            [bazel_binary]
            + bazelisk_flags()
            + common_startup_flags()
            + ["build"]
            + aggregated_flags
            + ["--"]
            + targets
        )
    except subprocess.CalledProcessError as e:
        handle_bazel_failure(e, "build")


def execute_bazel_build_with_kythe(bazel_version, bazel_binary, platform, flags, targets, bep_file):
    print_collapsed_group(":bazel: Computing flags for build step")
    aggregated_flags = compute_flags(
        platform,
        flags,
        bep_file,
        bazel_binary,
        enable_remote_cache=False,
    )

    print_expanded_group(":bazel: Build ({})".format(bazel_version))

    execute_command(
        [bazel_binary]
        + bazelisk_flags()
        + common_startup_flags()
        + kythe_startup_flags()
        + ["build"]
        + kythe_build_flags()
        + aggregated_flags
        + ["--"]
        + targets
    )


def calculate_targets(task_config, platform, bazel_binary, build_only, test_only):
    build_targets = [] if test_only else task_config.get("build_targets", [])
    test_targets = [] if build_only else task_config.get("test_targets", [])
    coverage_targets = [] if (build_only or test_only) else task_config.get("coverage_targets", [])
    index_targets = [] if (build_only or test_only) else task_config.get("index_targets", [])

    index_targets_query = (
        None if (build_only or test_only) else task_config.get("index_targets_query", None)
    )
    if index_targets_query:
        output = execute_command_and_get_output(
            [bazel_binary]
            + common_startup_flags()
            + ["--nosystem_rc", "--nohome_rc", "query", index_targets_query],
            print_output=False,
        )
        index_targets += output.strip().split("\n")

    # Remove the "--" argument splitter from the list that some configs explicitly
    # include. We'll add it back again later where needed.
    build_targets = [x.strip() for x in build_targets if x.strip() != "--"]
    test_targets = [x.strip() for x in test_targets if x.strip() != "--"]
    coverage_targets = [x.strip() for x in coverage_targets if x.strip() != "--"]
    index_targets = [x.strip() for x in index_targets if x.strip() != "--"]

    shard_id = int(os.getenv("BUILDKITE_PARALLEL_JOB", "-1"))
    shard_count = int(os.getenv("BUILDKITE_PARALLEL_JOB_COUNT", "-1"))
    if shard_id > -1 and shard_count > -1:
        print_collapsed_group(
            ":female-detective: Calculating targets for shard {}/{}".format(
                shard_id + 1, shard_count
            )
        )
        expanded_test_targets = expand_test_target_patterns(bazel_binary, platform, test_targets)
        test_targets = get_targets_for_shard(expanded_test_targets, shard_id, shard_count)

    return build_targets, test_targets, coverage_targets, index_targets


def expand_test_target_patterns(bazel_binary, platform, test_targets):
    included_targets, excluded_targets = partition_targets(test_targets)
    excluded_string = (
        " except tests(set({}))".format(" ".join("'{}'".format(t) for t in excluded_targets))
        if excluded_targets
        else ""
    )

    exclude_manual = ' except tests(attr("tags", "manual", set({})))'.format(
        " ".join("'{}'".format(t) for t in included_targets)
    )

    eprint("Resolving test targets via bazel query")
    output = execute_command_and_get_output(
        [bazel_binary]
        + common_startup_flags()
        + [
            "--nosystem_rc",
            "--nohome_rc",
            "query",
            "tests(set({})){}{}".format(
                " ".join("'{}'".format(t) for t in included_targets),
                excluded_string,
                exclude_manual,
            ),
        ],
        print_output=False,
    ).strip()
    return output.split("\n") if output else []


def partition_targets(targets):
    included_targets, excluded_targets = [], []
    for target in targets:
        if target.startswith("-"):
            excluded_targets.append(target[1:])
        else:
            included_targets.append(target)

    return included_targets, excluded_targets


def get_targets_for_shard(test_targets, shard_id, shard_count):
    # TODO(fweikert): implement a more sophisticated algorithm
    return sorted(test_targets)[shard_id::shard_count]


def execute_bazel_test(
    bazel_version,
    bazel_binary,
    platform,
    flags,
    targets,
    bep_file,
    monitor_flaky_tests,
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
        bep_file,
        bazel_binary,
        enable_remote_cache=not monitor_flaky_tests,
    )

    print_expanded_group(":bazel: Test ({})".format(bazel_version))
    try:
        execute_command(
            [bazel_binary]
            + bazelisk_flags()
            + common_startup_flags()
            + ["test"]
            + aggregated_flags
            + ["--"]
            + targets
        )
    except subprocess.CalledProcessError as e:
        handle_bazel_failure(e, "test")


def execute_bazel_coverage(bazel_version, bazel_binary, platform, flags, targets):
    aggregated_flags = [
        "--build_tests_only",
        "--local_test_jobs=" + concurrent_test_jobs(platform),
    ]
    print_collapsed_group(":bazel: Computing flags for coverage step")
    aggregated_flags += compute_flags(
        platform,
        flags,
        None,
        bazel_binary,
        enable_remote_cache=True,
    )

    print_expanded_group(":bazel: Coverage ({})".format(bazel_version))
    try:
        execute_command(
            [bazel_binary]
            + bazelisk_flags()
            + common_startup_flags()
            + ["coverage"]
            + aggregated_flags
            + ["--"]
            + targets
        )
    except subprocess.CalledProcessError as e:
        handle_bazel_failure(e, "coverage")


def upload_test_logs_from_bep(bep_file, tmpdir, monitor_flaky_tests):
    bazelci_agent_binary = download_bazelci_agent(tmpdir, "0.1.3")
    execute_command(
        [
            bazelci_agent_binary,
            "artifact",
            "upload",
            "--delay=5",
            "--mode=buildkite",
            "--build_event_json_file={}".format(bep_file),
        ]
        + (["--monitor_flaky_tests"] if monitor_flaky_tests else [])
    )


def upload_json_profile(json_profile_path, tmpdir):
    if not os.path.exists(json_profile_path):
        return
    print_collapsed_group(":gcloud: Uploading JSON Profile")
    execute_command(["buildkite-agent", "artifact", "upload", json_profile_path], cwd=tmpdir)


def upload_corrupted_outputs(capture_corrupted_outputs_dir, tmpdir):
    if not os.path.exists(capture_corrupted_outputs_dir):
        return
    print_collapsed_group(":gcloud: Uploading corrupted outputs")
    execute_command(
        ["buildkite-agent", "artifact", "upload", "{}/**/*".format(capture_corrupted_outputs_dir)],
        cwd=tmpdir,
    )


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


def execute_command(args, shell=False, fail_if_nonzero=True, cwd=None, print_output=True):
    if print_output:
        eprint(" ".join(args))
    return subprocess.run(
        args, shell=shell, check=fail_if_nonzero, env=os.environ, cwd=cwd
    ).returncode


def execute_command_background(args):
    eprint(" ".join(args))
    return subprocess.Popen(args, env=os.environ)


def terminate_background_process(process):
    if process:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def create_step(label, commands, platform, shards=1, soft_fail=None):
    if "docker-image" in PLATFORMS[platform]:
        step = create_docker_step(
            label,
            image=PLATFORMS[platform]["docker-image"],
            commands=commands,
            queue=PLATFORMS[platform].get("queue", "default"),
            always_pull=PLATFORMS[platform].get("always-pull", True),
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

    if soft_fail is not None:
        step["soft_fail"] = soft_fail

    # Enforce a global 8 hour job timeout.
    step["timeout_in_minutes"] = 8 * 60

    # Automatically retry when an agent got lost (usually due to an infra flake).
    step["retry"] = {
        "automatic": [
            {"exit_status": -1, "limit": 3},  # Buildkite internal "agent lost" exit code
            {"exit_status": 137, "limit": 3},  # SIGKILL
            {"exit_status": 143, "limit": 3},  # SIGTERM
        ]
    }

    return step


def create_docker_step(
    label, image, commands=None, additional_env_vars=None, queue="default", always_pull=True
):
    env = ["ANDROID_HOME", "ANDROID_NDK_HOME", "BUILDKITE_ARTIFACT_UPLOAD_DESTINATION"]
    if additional_env_vars:
        env += ["{}={}".format(k, v) for k, v in additional_env_vars.items()]

    step = {
        "label": label,
        "command": commands,
        "agents": {"queue": queue},
        "plugins": {
            "docker#v3.8.0": {
                "always-pull": always_pull,
                "environment": env,
                "image": image,
                "network": "host",
                "privileged": True,
                "propagate-environment": True,
                "propagate-uid-gid": True,
                "volumes": [
                    "/etc/group:/etc/group:ro",
                    "/etc/passwd:/etc/passwd:ro",
                    "/etc/shadow:/etc/shadow:ro",
                    "/opt/android-ndk-r15c:/opt/android-ndk-r15c:ro",
                    "/opt/android-ndk-r25b:/opt/android-ndk-r25b:ro",
                    "/opt/android-sdk-linux:/opt/android-sdk-linux:ro",
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
    notify,
):
    task_configs = configs.get("tasks", None)
    if not task_configs:
        raise BuildkiteException("{0} pipeline configuration is empty.".format(project_name))

    pipeline_steps = []
    # If the repository is hosted on Git-on-borg, we show the link to the commit Gerrit review
    buildkite_repo = os.getenv("BUILDKITE_REPO")
    if is_git_on_borg_repo(buildkite_repo):
        show_gerrit_review_link(buildkite_repo, pipeline_steps)

    task_configs = filter_tasks_that_should_be_skipped(task_configs, pipeline_steps)

    # In Bazel Downstream Project pipelines, git_repository and project_name must be specified.
    is_downstream_project = use_but and git_repository and project_name

    buildifier_config = configs.get("buildifier")
    # Skip Buildifier when we test downstream projects.
    if buildifier_config and not is_downstream_project:
        buildifier_env_vars = {}
        if isinstance(buildifier_config, str):
            # Simple format:
            # ---
            # buildifier: latest
            buildifier_env_vars["BUILDIFIER_VERSION"] = buildifier_config
        else:
            # Advanced format:
            # ---
            # buildifier:
            #   version: latest
            #   warnings: all
            if "version" in buildifier_config:
                buildifier_env_vars["BUILDIFIER_VERSION"] = buildifier_config["version"]
            if "warnings" in buildifier_config:
                buildifier_env_vars["BUILDIFIER_WARNINGS"] = buildifier_config["warnings"]

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
    skipped_due_to_bazel_version = []
    for task, task_config in task_configs.items():
        platform = get_platform_for_task(task, task_config)
        task_name = task_config.get("name")
        soft_fail = task_config.get("soft_fail")

        # We override the Bazel version in downstream pipelines. This means that two tasks that
        # only differ in the value of their explicit "bazel" field will be identical in the
        # downstream pipeline, thus leading to duplicate work.
        # Consequently, we filter those duplicate tasks here.
        if is_downstream_project:
            h = hash_task_config(task, task_config)
            if h in config_hashes:
                skipped_due_to_bazel_version.append(
                    "{}: '{}'".format(
                        create_label(platform, project_name, task_name=task_name),
                        task_config.get("bazel", "latest"),
                    )
                )
            config_hashes.add(h)

        shards = task_config.get("shards", "1")
        try:
            shards = int(shards)
        except ValueError:
            raise BuildkiteException("Task {} has invalid shard value '{}'".format(task, shards))

        step = runner_step(
            platform=platform,
            task=task,
            task_name=task_name,
            project_name=project_name,
            http_config=http_config,
            file_config=file_config,
            git_repository=git_repository,
            git_commit=git_commit,
            monitor_flaky_tests=monitor_flaky_tests,
            use_but=use_but,
            shards=shards,
            soft_fail=soft_fail,
        )
        pipeline_steps.append(step)

    if skipped_due_to_bazel_version:
        lines = ["\n- {}".format(s) for s in skipped_due_to_bazel_version]
        commands = [
            "buildkite-agent annotate --style=info '{}' --append --context 'ctx-skipped_due_to_bazel_version'".format(
                "".join(lines)
            ),
            "buildkite-agent meta-data set 'has-skipped-steps' 'true'",
        ]
        pipeline_steps.append(
            create_step(
                label=":pipeline: Print information about skipped tasks due to different Bazel versions",
                commands=commands,
                platform=DEFAULT_PLATFORM,
            )
        )

    pipeline_slug = os.getenv("BUILDKITE_PIPELINE_SLUG")
    all_downstream_pipeline_slugs = []
    for _, config in DOWNSTREAM_PROJECTS.items():
        all_downstream_pipeline_slugs.append(config["pipeline_slug"])
    # We update last green commit in the following cases:
    #   1. This job runs on master, stable or main branch (could be a custom build launched manually)
    #   2. We intend to run the same job in downstream with Bazel@HEAD (eg. google-bazel-presubmit)
    #   3. This job is not:
    #      - a GitHub pull request
    #      - uses a custom built Bazel binary (in Bazel Downstream Projects pipeline)
    #      - testing incompatible flags
    #      - running `bazelisk --migrate` in a non-downstream pipeline
    if (
        current_branch_is_main_branch()
        and pipeline_slug in all_downstream_pipeline_slugs
        and not (is_pull_request() or use_but or use_bazelisk_migrate())
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

    if use_bazelisk_migrate() and not is_downstream_project:
        # Print results of bazelisk --migrate in project pipelines that explicitly set
        # the USE_BAZELISK_MIGRATE env var, but that are not being run as part of a
        # downstream pipeline.
        number = os.getenv("BUILDKITE_BUILD_NUMBER")
        pipeline_steps += get_steps_for_aggregating_migration_results(number, notify)

    print_pipeline_steps(pipeline_steps, handle_emergencies=not is_downstream_project)


def show_gerrit_review_link(git_repository, pipeline_steps):
    host = re.search(r"https://(.+?)\.googlesource", git_repository).group(1)
    if not host:
        raise BuildkiteException("Couldn't get host name from %s" % git_repository)
    text = "The transformed code used in this pipeline can be found under https://{}-review.googlesource.com/q/{}".format(
        host, os.getenv("BUILDKITE_COMMIT")
    )
    commands = ["buildkite-agent annotate --style=info '{}'".format(text)]
    pipeline_steps.append(
        create_step(
            label=":pipeline: Print information about Gerrit Review Link",
            commands=commands,
            platform=DEFAULT_PLATFORM,
        )
    )


def is_git_on_borg_repo(git_repository):
    return git_repository and "googlesource.com" in git_repository


def hash_task_config(task_name, task_config):
    # Two task configs c1 and c2 have the same hash iff they lead to two functionally identical jobs
    # in the downstream pipeline. This function discards the "bazel" field (since it's being
    # overridden) and the "name" field (since it has no effect on the actual work).
    # Moreover, it adds an explicit "platform" field if that's missing.
    cpy = task_config.copy()
    cpy.pop("bazel", None)
    cpy.pop("name", None)
    if "platform" not in cpy:
        cpy["platform"] = task_name

    m = hashlib.md5()
    # Technically we should sort cpy[key] if it's a list of entries
    # whose order does not matter (e.g. targets).
    # However, this seems to be overkill for the current use cases.
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
        path
        for path in output.split("\n")
        if path.startswith(".bazelci/") and os.path.splitext(path)[1] in CONFIG_FILE_EXTENSIONS
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
    shards=1,
    soft_fail=None,
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
    label = create_label(platform, project_name, task_name=task_name)
    return create_step(
        label=label,
        commands=[fetch_bazelcipy_command(), command],
        platform=platform,
        shards=shards,
        soft_fail=soft_fail,
    )


def fetch_bazelcipy_command():
    return "curl -sS {0} -o bazelci.py".format(SCRIPT_URL)


def fetch_aggregate_incompatible_flags_test_result_command():
    return "curl -sS {0} -o aggregate_incompatible_flags_test_result.py".format(
        AGGREGATE_INCOMPATIBLE_TEST_RESULT_URL
    )


def upload_project_pipeline_step(project_name, git_repository, http_config, file_config):
    pipeline_command = (
        '{0} bazelci.py project_pipeline --project_name="{1}" ' + "--git_repository={2}"
    ).format(PLATFORMS[DEFAULT_PLATFORM]["python"], project_name, git_repository)
    pipeline_command += " --use_but"
    if http_config:
        pipeline_command += " --http_config=" + http_config
    if file_config:
        pipeline_command += " --file_config=" + file_config
    pipeline_command += " | tee /dev/tty | buildkite-agent pipeline upload"

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

    step = create_step(
        label=create_label(platform, project_name, build_only, test_only),
        commands=[fetch_bazelcipy_command(), pipeline_command],
        platform=platform,
    )
    # Always try to automatically retry the bazel build step, this will make
    # the publish bazel binaries pipeline more reliable.
    step["retry"] = {
        "automatic": [
            {"exit_status": "*", "limit": 3},
        ]
    }
    return step


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

    # We can skip this check if we're not on the main branch, because then we're probably
    # building a one-off custom debugging binary anyway.
    if current_branch_is_main_branch():
        missing = expected_platforms.difference(configured_platforms)
        if missing:
            raise BuildkiteException(
                (
                    "Bazel publish binaries pipeline needs to build Bazel for every commit on all publish_binary-enabled platforms. "
                    "Please add jobs for the missing platform(s) to the pipeline config: {}".format(
                        ", ".join(missing)
                    )
                )
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
    Return a list of incompatible flags to be tested. The key is the flag name and the value is its Github URL.
    """
    output = subprocess.check_output(
        [
            # Query for open issues with "incompatible-change" and "migration-ready" label.
            "curl",
            "https://api.github.com/search/issues?per_page=100&q=repo:bazelbuild/bazel+label:incompatible-change+label:migration-ready+state:open",
        ]
    ).decode("utf-8")
    issue_info = json.loads(output)

    FLAG_PATTERN = re.compile(r"^--[a-z][a-z0-9_]*$")
    incompatible_flags = {}
    for issue in issue_info["items"]:
        name = "--" + issue["title"].split(":")[0]
        url = issue["html_url"]
        if FLAG_PATTERN.match(name):
            incompatible_flags[name] = url
        else:
            eprint(
                f"{name} is not recognized as an incompatible flag, please modify the issue title "
                f'of {url} to "<incompatible flag name (without --)>:..."'
            )

    # If INCOMPATIBLE_FLAGS is set manually, we test those flags, try to keep the URL info if possible.
    if "INCOMPATIBLE_FLAGS" in os.environ:
        given_incompatible_flags = {}
        for flag in os.environ["INCOMPATIBLE_FLAGS"].split(","):
            given_incompatible_flags[flag] = incompatible_flags.get(flag, "")
        return given_incompatible_flags

    return incompatible_flags


def print_bazel_downstream_pipeline(
    task_configs, http_config, file_config, test_disabled_projects, notify
):
    pipeline_steps = []

    info_box_step = print_disabled_projects_info_box_step()
    if info_box_step is not None:
        pipeline_steps.append(info_box_step)

    if not use_bazelisk_migrate():
        if not task_configs:
            raise BuildkiteException("Bazel downstream pipeline configuration is empty.")
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
    else:
        incompatible_flags_map = fetch_incompatible_flags()
        if not incompatible_flags_map:
            step = create_step(
                label="No Incompatible flags info",
                commands=[
                    'buildkite-agent annotate --style=error "No incompatible flag issue is found on github for current version of Bazel." --context "noinc"'
                ],
                platform=DEFAULT_PLATFORM,
            )
            pipeline_steps.append(step)
            print_pipeline_steps(pipeline_steps)
            return

        info_box_step = print_incompatible_flags_info_box_step(incompatible_flags_map)
        if info_box_step is not None:
            pipeline_steps.append(info_box_step)

    pipeline_steps.append(
        create_step(
            label="Print skipped tasks annotation",
            commands=[
                'buildkite-agent annotate --style=info "The following tasks were skipped since they require specific Bazel versions:\n" --context "ctx-skipped_due_to_bazel_version"'
            ],
            platform=DEFAULT_PLATFORM,
        )
    )
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
                )
            )

    pipeline_steps.append({"wait": "~", "continue_on_failure": "true"})
    pipeline_steps.append(
        create_step(
            label="Remove skipped tasks annotation if unneeded",
            commands=[
                'buildkite-agent meta-data exists "has-skipped-steps" || buildkite-agent annotation remove --context "ctx-skipped_due_to_bazel_version"'
            ],
            platform=DEFAULT_PLATFORM,
        )
    )

    if use_bazelisk_migrate():
        current_build_number = os.environ.get("BUILDKITE_BUILD_NUMBER", None)
        if not current_build_number:
            raise BuildkiteException("Not running inside Buildkite")

        pipeline_steps += get_steps_for_aggregating_migration_results(current_build_number, notify)

    if (
        not test_disabled_projects
        and not use_bazelisk_migrate()
        and current_branch_is_main_branch()
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


def get_steps_for_aggregating_migration_results(current_build_number, notify):
    parts = [
        PLATFORMS[DEFAULT_PLATFORM]["python"],
        "aggregate_incompatible_flags_test_result.py",
        "--build_number=%s" % current_build_number,
    ]
    if notify:
        parts.append("--notify")
    return [
        {"wait": "~", "continue_on_failure": "true"},
        create_step(
            label="Aggregate incompatible flags test result",
            commands=[
                fetch_bazelcipy_command(),
                fetch_aggregate_incompatible_flags_test_result_command(),
                " ".join(parts),
            ],
            platform=DEFAULT_PLATFORM,
        ),
    ]


def bazelci_builds_download_url(platform, git_commit):
    bucket_name = "bazel-testing-builds" if THIS_IS_TESTING else "bazel-builds"
    return "https://storage.googleapis.com/{}/artifacts/{}/{}/bazel".format(
        bucket_name, platform, git_commit
    )


def bazelci_builds_nojdk_download_url(platform, git_commit):
    bucket_name = "bazel-testing-builds" if THIS_IS_TESTING else "bazel-builds"
    return "https://storage.googleapis.com/{}/artifacts/{}/{}/bazel_nojdk".format(
        bucket_name, platform, git_commit
    )


def bazelci_builds_gs_url(platform, git_commit):
    bucket_name = "bazel-testing-builds" if THIS_IS_TESTING else "bazel-builds"
    return "gs://{}/artifacts/{}/{}/bazel".format(bucket_name, platform, git_commit)


def bazelci_builds_nojdk_gs_url(platform, git_commit):
    bucket_name = "bazel-testing-builds" if THIS_IS_TESTING else "bazel-builds"
    return "gs://{}/artifacts/{}/{}/bazel_nojdk".format(bucket_name, platform, git_commit)


def bazelci_latest_build_metadata_url():
    bucket_name = "bazel-testing-builds" if THIS_IS_TESTING else "bazel-builds"
    return "gs://{}/metadata/latest.json".format(bucket_name)


def bazelci_builds_metadata_url(git_commit):
    bucket_name = "bazel-testing-builds" if THIS_IS_TESTING else "bazel-builds"
    return "gs://{}/metadata/{}.json".format(bucket_name, git_commit)


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

    # Find any failing steps other than Buildifier and steps with soft_fail enabled then "try update last green".
    def has_failed(job):
        state = job.get("state")
        # Ignore steps that don't have a state (like "wait").
        return (
            state is not None
            and state != "passed"
            and not job.get("soft_failed")
            and job["id"] != current_job_id
            and job["name"] != BUILDIFIER_STEP_NAME
        )

    failing_jobs = [j["name"] for j in build_info["jobs"] if has_failed(j)]
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
        success = False
        try:
            execute_command(["git", "fetch", "-v", "origin", last_green_commit])
            success = True
        except subprocess.CalledProcessError:
            # If there was an error fetching the commit it typically means
            # that the commit does not exist anymore - due to a force push. In
            # order to recover from that assume that the current commit is the
            # newest commit.
            result = [current_commit]
        finally:
            if success:
                result = (
                    subprocess.check_output(
                        ["git", "rev-list", "%s..%s" % (last_green_commit, current_commit)]
                    )
                    .decode("utf-8")
                    .strip()
                )
    else:
        result = None

    # If current_commit is newer that last_green_commit, `git rev-list A..B` will output a bunch of
    # commits, otherwise the output should be empty.
    if not last_green_commit or result:
        execute_command(
            [
                "echo %s | %s -h 'Cache-Control: no-store' cp - %s"
                % (current_commit, gsutil_command(), last_green_commit_url)
            ],
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
    generation = None
    output = None
    for attempt in range(5):
        output = subprocess.check_output(
            [gsutil_command(), "stat", bazelci_latest_build_metadata_url()], env=os.environ
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
            [gsutil_command(), "cat", bazelci_latest_build_metadata_url()], env=os.environ
        )
        hasher = hashlib.md5()
        hasher.update(output)
        actual_md5hash = hasher.digest()

        if expected_md5hash == actual_md5hash:
            break
    info = json.loads(output.decode("utf-8"))
    return generation, info["build_number"]


def sha256_hexdigest(filename):
    sha256 = hashlib.sha256()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
    return sha256.hexdigest()


def upload_bazel_binaries():
    """
    Uploads all Bazel binaries to a deterministic URL based on the current Git commit.

    Returns maps of platform names to sha256 hashes of the corresponding bazel and bazel_nojdk binaries.
    """
    bazel_hashes = {}
    bazel_nojdk_hashes = {}
    for platform_name, platform in PLATFORMS.items():
        if not should_publish_binaries_for_platform(platform_name):
            continue
        tmpdir = tempfile.mkdtemp()
        try:
            bazel_binary_path = download_bazel_binary(tmpdir, platform_name)
            # One platform that we build on can generate binaries for multiple platforms, e.g.
            # the centos7 platform generates binaries for the "centos7" platform, but also
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
                bazel_hashes[target_platform_name] = sha256_hexdigest(bazel_binary_path)

            # Also publish bazel_nojdk binaries.
            bazel_nojdk_binary_path = download_bazel_nojdk_binary(tmpdir, platform_name)
            for target_platform_name in platform["publish_binary"]:
                execute_command(
                    [
                        gsutil_command(),
                        "cp",
                        bazel_nojdk_binary_path,
                        bazelci_builds_nojdk_gs_url(
                            target_platform_name, os.environ["BUILDKITE_COMMIT"]
                        ),
                    ]
                )
                bazel_nojdk_hashes[target_platform_name] = sha256_hexdigest(bazel_nojdk_binary_path)
        except subprocess.CalledProcessError as e:
            # If we're not on the main branch, we're probably building a custom one-off binary and
            # ignore failures for individual platforms (it's possible that we didn't build binaries
            # for all platforms).
            if not current_branch_is_main_branch():
                eprint(
                    "Ignoring failure to download and publish Bazel binary for platform {}: {}".format(
                        platform_name, e
                    )
                )
            else:
                raise e
        finally:
            shutil.rmtree(tmpdir)
    return bazel_hashes, bazel_nojdk_hashes


def try_publish_binaries(bazel_hashes, bazel_nojdk_hashes, build_number, expected_generation):
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
    for platform, sha256 in bazel_hashes.items():
        info["platforms"][platform] = {
            "url": bazelci_builds_download_url(platform, git_commit),
            "sha256": sha256,
            "nojdk_url": bazelci_builds_nojdk_download_url(platform, git_commit),
            "nojdk_sha256": bazel_nojdk_hashes[platform],
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
                    bazelci_latest_build_metadata_url(),
                ]
            )
        except subprocess.CalledProcessError:
            raise BinaryUploadRaceException()

        execute_command(
            [
                gsutil_command(),
                "cp",
                bazelci_latest_build_metadata_url(),
                bazelci_builds_metadata_url(git_commit),
            ]
        )
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
    bazel_hashes, bazel_nojdk_hashes = upload_bazel_binaries()

    # Try to update the info.json with data about our build. This will fail (expectedly) if we're
    # not the latest build. Only do this if we're building binaries from the main branch to avoid
    # accidentally publishing a custom debug build as the "latest" Bazel binary.
    if current_branch_is_main_branch():
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
                try_publish_binaries(
                    bazel_hashes, bazel_nojdk_hashes, current_build_number, latest_generation
                )
            except BinaryUploadRaceException:
                # Retry.
                continue

            eprint(
                "Successfully updated '{0}' to binaries from build {1}.".format(
                    bazelci_latest_build_metadata_url(), current_build_number
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
        "--test_disabled_projects", type=bool, nargs="?", const=True
    )
    bazel_downstream_pipeline.add_argument("--notify", type=bool, nargs="?", const=True)

    project_pipeline = subparsers.add_parser("project_pipeline")
    project_pipeline.add_argument("--project_name", type=str)
    project_pipeline.add_argument("--file_config", type=str)
    project_pipeline.add_argument("--http_config", type=str)
    project_pipeline.add_argument("--git_repository", type=str)
    project_pipeline.add_argument("--monitor_flaky_tests", type=bool, nargs="?", const=True)
    project_pipeline.add_argument("--use_but", type=bool, nargs="?", const=True)
    project_pipeline.add_argument("--notify", type=bool, nargs="?", const=True)

    runner = subparsers.add_parser("runner")
    runner.add_argument("--task", action="store", type=str, default="")
    runner.add_argument("--file_config", type=str)
    runner.add_argument("--http_config", type=str)
    runner.add_argument("--git_repository", type=str)
    runner.add_argument(
        "--git_commit", type=str, help="Reset the git repository to this commit after cloning it"
    )
    runner.add_argument(
        "--repo_location",
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

    subparsers.add_parser("publish_binaries")
    subparsers.add_parser("try_update_last_green_commit")
    subparsers.add_parser("try_update_last_green_downstream_commit")

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
            # If USE_BAZELISK_MIGRATE is true, we don't need to fetch task configs for Bazel
            # since we use Bazelisk to fetch Bazel binaries.
            configs = (
                {} if use_bazelisk_migrate() else fetch_configs(args.http_config, args.file_config)
            )
            print_bazel_downstream_pipeline(
                task_configs=configs.get("tasks", None),
                http_config=args.http_config,
                file_config=args.file_config,
                test_disabled_projects=args.test_disabled_projects,
                notify=args.notify,
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
                notify=args.notify,
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

            # The value of `BUILDKITE_MESSAGE` defaults to the commit message, which can be too large
            # on Windows, therefore we truncate the value to 1000 characters.
            # See https://github.com/bazelbuild/continuous-integration/issues/1218
            if "BUILDKITE_MESSAGE" in os.environ:
                os.environ["BUILDKITE_MESSAGE"] = os.environ["BUILDKITE_MESSAGE"][:1000]

            execute_commands(
                task_config=task_config,
                platform=platform,
                git_repository=args.git_repository,
                git_commit=args.git_commit,
                repo_location=args.repo_location,
                use_bazel_at_commit=args.use_bazel_at_commit,
                use_but=args.use_but,
                save_but=args.save_but,
                needs_clean=args.needs_clean,
                build_only=args.build_only,
                test_only=args.test_only,
                monitor_flaky_tests=args.monitor_flaky_tests,
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
