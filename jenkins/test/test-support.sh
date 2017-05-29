#!/bin/bash
#
# Copyright 2017 The Bazel Authors. All rights reserved.
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

# Utilities to write integration test that run jenkins inside docker
# and interrogate the jenkins master.

DOCKER="${PYTHON_RUNFILES}/docker/docker"
source "${PYTHON_RUNFILES}/io_bazel_ci/jenkins/test/common.sh"

set -e

# Machine on which the docker daemon is running, default is localhost.
: ${DOCKER_SERVER:=127.0.0.1}

setup() {
  __test_support_containers="$(test_setup "${DOCKER_SERVER}" 0)"
  __test_support_port=$(get_jenkins_port ${__test_support_containers})
  __test_support_diagnostics=
}

teardown() {
  local jenkins="$(f() { echo $1; }; f ${__test_support_containers})"
  local logs="$(docker logs $jenkins)"
  kill_containers ${__test_support_containers}
  if [ -n "${__test_support_diagnostics}" ]; then
    >&2 echo '
*** LOG FROM THE JENKINS MASTER ***
'"${logs}"'

*** FAILURES SUMMARY ***
'"${__test_support_diagnostics}
"
  exit 1
  else
    >&2 echo '

*** ALL TESTS PASSED ***
'
  fi
}

# Utilities
mcurl() {
  local url="$1"
  shift 1
  # Since we are connecting to localhost and we tested the server is up and running,
  # we limit the request to 1 seconds for connection and 10 seconds total
  curl --connect-timeout 1 -m 10 -s "http://${DOCKER_SERVER}:${__test_support_port}${url}" "$@"
}

get_status_code() {
  mcurl "$1" -I -L | grep '^HTTP/' | tail -1 | cut -d " " -f 2
}

diagnostics=
report() {
  echo "FAILED: $*" >&2
  __test_support_diagnostics="${__test_support_diagnostics}
$*"
}

test_status_code() {
  local code="$(get_status_code "$1")"
  if [ "$code" != "$2" ]; then
    report "Got status $code while expecting $2 from $1"
  else
    echo "OK $1 returned $2"
  fi
}

test_ok_status() {
  test_status_code "$1" 200
}
