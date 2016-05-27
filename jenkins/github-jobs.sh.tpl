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

set -e
set +x

BAZEL=~/.bazel/${BAZEL_VERSION}/bin/bazel

ROOT="${PWD}"

TEST_TAG_FILTERS="{{ variables.TEST_TAG_FILTERS }}"
JAVA_VERSION="1.8"
if [[ "${BAZEL_VERSION}" =~ -jdk7$ ]]; then
  JAVA_VERSION="1.7"
  if [ -n "${TEST_TAG_FILTERS}" ]; then
    TEST_TAG_FILTERS="${TEST_TAG_FILTERS},-jdk8"
  else
    TEST_TAG_FILTERS="-jdk8"
  fi
fi

cat >${ROOT}/bazel.bazelrc <<EOF
build {{ variables.BUILD_OPTS }}
test {{ variables.TEST_OPTS }}
test --test_tag_filters ${TEST_TAG_FILTERS}
test --define JAVA_VERSION=${JAVA_VERSION}
EOF

if [[ "${PLATFORM_NAME}" =~ .*darwin.* ]] && \
      xcodebuild -showsdks 2> /dev/null | grep -q '\-sdk iphonesimulator'; then
  cat >>${ROOT}/bazel.bazelrc <<EOF
build --define IPHONE_SDK=1
EOF
fi

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

echo "==== bazel version ===="
bazel version
echo
echo

set -x

{{ variables.CONFIGURE }}
TESTS='{{ variables.TESTS }}'
[ -z "${TESTS}" ] || TESTS="$(bazel query "tests(${TESTS})")"
[ -z "{{ variables.BUILDS }}" ] || bazel build {{ variables.BUILDS }}
[ -z "${TESTS}" ] || bazel test ${TESTS}
