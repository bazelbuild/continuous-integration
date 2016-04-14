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
INSTALLER_PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m)
if [ "$BAZEL_VERSION" = "HEAD" ]; then
  export BAZEL_INSTALLER=$(find $PWD/bazel-installer -name '*.sh' | \
      fgrep "PLATFORM_NAME=${INSTALLER_PLATFORM}" | fgrep -v jdk7 | head -1)
else
  if [ "$BAZEL_VERSION" = "latest" ]; then
    URL=$(curl -L https://github.com/bazelbuild/bazel/releases/latest | \
      grep -o '"/.*/bazel-.*-installer-'${INSTALLER_PLATFORM}'.sh"' | grep -v jdk7 | sed 's/"//g')
  else
    URL=https://github.com/bazelbuild/bazel/releases/download/${BAZEL_VERSION}/bazel-${BAZEL_VERSION}-installer-${INSTALLER_PLATFORM}.sh
  fi
  export BAZEL_INSTALLER=${PWD}/bazel-installer/install.sh
  curl -L -o ${BAZEL_INSTALLER} https://github.com${URL}
fi
BASE="${PWD}/bazel-install"
mkdir -p "${BASE}/binary"

bash "${BAZEL_INSTALLER}" \
  --base="${BASE}" \
  --bazelrc="${BASE}/binary/bazel.bazelrc" \
  --bin="${BASE}/binary"

cat >>${BASE}/bazel.bazelrc <<EOF
build {{ variables.BUILD_OPTS }}
test {{ variables.TEST_OPTS }}
EOF

ROOT="${PWD}"
rm -f .unstable
cd {{ variables.WORKSPACE }}
function bazel() {
  local retCode=0
  ${BASE}/binary/bazel --bazelrc=${BASE}/bazel.bazelrc "$@" || retCode=$?
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
