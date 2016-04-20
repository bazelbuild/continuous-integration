#!/bin/bash
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

# Shell script containing the main build phase for all bazel_github_job-s

set -x
BAZEL=~/.bazel/${BAZEL_VERSION}/bin/bazel

ROOT="${PWD}"

cat >>${ROOT}/bazel.bazelrc <<EOF
build {{ variables.BUILD_OPTS }}
test {{ variables.TEST_OPTS }}
EOF

rm -f .unstable
cd {{ variables.WORKSPACE }}
function bazel() {
  local retCode=0
  ${BAZEL} --bazelrc=${ROOT}/bazel.bazelrc "$@" || retCode=$?
  if (( $retCode == 3 )); then
    echo 1 >"${ROOT}/.unstable"
  elif (( $retCode != 0 )); then
    exit $retCode
  fi
}
{{ variables.CONFIGURE }}
TESTS="$(bazel query 'tests({{ variables.TESTS }})')"
[ -z "{{ variables.BUILDS }}" ] || bazel build {{ variables.BUILDS }}
[ -z "${TESTS}" ] || bazel test ${TESTS}
