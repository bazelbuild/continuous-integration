#!/bin/bash
#
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

# Runs the jenkins test images inside the docker container.
# Just a wrapper script to use the test support in run mode

# So that the docker incremental loader knows where the runfiles are.
export PYTHON_RUNFILES="${PYTHON_RUNFILES:-${BASH_SOURCE[0]}.runfiles}"
cd "${PYTHON_RUNFILES}"
PYTHON_RUNFILES="${PWD}"

source "${PYTHON_RUNFILES}/io_bazel_ci/jenkins/test/common.sh"

set -e

# Port to serve Jenkins on, default is 8080.
PORT=8080

# Machine on which the docker daemon is running, default is localhost.
: ${DOCKER_SERVER:=127.0.0.1}

VOLUMES=()
while getopts ":p:h:s:" opt; do
  case "${opt}" in
    p)
      PORT="${OPTARG}"
      ;;
    h)
      VOLUMES=(-v "${OPTARG}:/var/jenkins_home")
      ;;
    s)
      VOLUMES=(-v "${OPTARG}:/opt/secrets")
      ;;
    *)
      echo "Usage: $0 [-p <port>] [-s </volumes/secrets>] [-h </volumes/jenkins_home>]" >&2
      exit 1
      ;;
  esac
done

containers="$(test_setup "${DOCKER_SERVER}" "${PORT}" "${VOLUMES[@]}")"
attach ${containers}
kill_containers ${containers}
