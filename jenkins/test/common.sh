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
# TODO(dmarting): should certainly centralize everything around docker testing
# in the docker rules and replace that.

: ${DOCKER:=docker}

load_images() {
  # Load all images.
  "${PYTHON_RUNFILES}/io_bazel_ci/jenkins/ubuntu-docker.docker"
  "${PYTHON_RUNFILES}/io_bazel_ci/jenkins/deploy.docker"
  "${PYTHON_RUNFILES}/io_bazel_ci/jenkins/jenkins-test"
}

run_jenkins_master() {
  # Run main container, serving jenkins on port provided by the first argument,
  # defaulting to 8080.
  local server="${1:-127.0.0.1}"
  local port="${2:-8080}"
  shift 2
  ${DOCKER} run -d \
	 --env JENKINS_SERVER="http://jenkins:${port}" \
	 -p "${server}:${port}:8080" \
	 "$@" \
	 bazel/jenkins:jenkins-test
}

get_jenkins_port() {
  # Return the port in which the jenkins master has been mapped to
  ${DOCKER} port "$1" 8080 | cut -d ":" -f 2
}

test_http() {
  return [[ "$(curl -sI "$1")" =~ ^HTTP/[0-9.]+\ 2 ]]
}

# Wait for jenkins to start-up for at most 3 minutes
wait_for_server() {
  local server="${1:-localhost}"
  local port="${2:-8080}"
  local timeout=180
  local ts="$(date +%s)"
  echo -n "*** Waiting for jenkins server to be up and running on port ${port}"
  while ! [[ "$(curl -sI  "http://${server}:${port}/jnlpJars/slave.jar")" =~ ^HTTP/[0-9.]+\ 2 ]]
  do
    echo -n "."
    sleep 1
    if (( "$(date +%s)" - "$ts" > "$timeout" )); then
      echo
      echo "Failed to connect to Jenkins, aborting..." >&2
      exit 1
    fi
  done
  echo " ok."
}

run_containers() {
  # Run the executor nodes, in priviledged mode for Bazel.
  local jenkins="$1"
  ${DOCKER} run -d --privileged=true \
         --link "${jenkins}:jenkins" --env "JENKINS_SERVER=http://jenkins:8080" \
         bazel/jenkins:ubuntu-docker.docker
  ${DOCKER} run -d --privileged=true \
         --link "${jenkins}:jenkins" --env "JENKINS_SERVER=http://jenkins:8080" \
         bazel/jenkins:deploy.docker
}

kill_containers() {
  # Kill containers and remove them
  for i in "$@"; do
    ${DOCKER} rm -f "$i" &>/dev/null || true
  done
}

test_setup() {
  # Setup the test and returns the list of started-up containers, the master first
  local server="${1:-localhost}"
  local port="${2:-0}"
  shift 2
  load_images >&2
  local jenkins="$(run_jenkins_master "${server}" "${port}" "$@")"
  port=$(get_jenkins_port "${jenkins}")
  wait_for_server "${server}" "${port}" >&2
  local containers="$(run_containers "${jenkins}" | xargs)"
  echo "$jenkins $containers"
}

attach() {
  # Attach to the first containers passed in argument
  ${DOCKER} attach "$1"
}

