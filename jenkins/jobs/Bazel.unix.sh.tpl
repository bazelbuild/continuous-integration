#!/usr/bin/env bash
# Copyright 2016 The Bazel Authors. All rights reserved.
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

# Shell script to set-up the environment on Linux and Darwin to bootstrap
# bazel.

source scripts/ci/build.sh

export BUILD_BY="Jenkins"
export BUILD_LOG="${BUILD_URL}"
export GIT_REPOSITORY_URL="${GIT_URL}"
export BAZEL_COMPILE_TARGET="compile,srcs,determinism"
if [ "${JAVA_VERSION}" = "1.7" ]
then
  export BOOTSTRAP_BAZEL="${HOME}/.bazel/latest-jdk7/binary/bazel"
  if [[ "${PLATFORM_NAME}" =~ "freebsd" ]] ; then
      echo "Skipping building bazel of freebsd with java 7"
      exit 0
  fi
else
  export BOOTSTRAP_BAZEL="${HOME}/.bazel/latest/binary/bazel"
fi

if [[ "${NODE_LABELS}" =~ "no-release" ]]; then
  bazel_build
else
  bazel_build output/ci
fi

