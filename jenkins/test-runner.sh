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

# So that the docker incremental loader knows where the runfiles are.
export PYTHON_RUNFILES="${PYTHON_RUNFILES:-${BASH_SOURCE[0]}.runfiles}"
cd "${PYTHON_RUNFILES}"
PYTHON_RUNFILES="${PWD}"

# Port to serve Jenkins on, default is 8080.
PORT="8080"

# Machine on which the docker daemon is running, default is localhost.
: ${DOCKER_SERVER:=localhost}

VOLUMES=()
while getopts ":p:h:s:" opt; do
  case "${opt}" in
    p)
      PORT="${OPTARG}"
      ;;
    h)
      VOLUMES=(-v "${OPTARG}:/volumes/jenkins_home")
      ;;
    s)
      VOLUMES=(-v "${OPTARG}:/volumes/secrets")
      ;;
    *)
      echo "Usage: $0 [-p <port>] [-s </volumes/secrets>] [-h </volumes/jenkins_home>]" >&2
      exit 1
      ;;
  esac
done

# Load all images.
./io_bazel_ci/jenkins/ubuntu-docker.docker
./io_bazel_ci/jenkins/deploy.docker
./io_bazel_ci/jenkins/jenkins-test

# Run main container, serving jenkins on port provided by the first argument,
# defaulting to 8080.
docker rm -f jenkins &> /dev/null  # Remove latent jenkins instance.
docker run -d \
  --env JENKINS_SERVER="http://jenkins:${PORT}" \
  --name jenkins \
  "${VOLUMES[@]}" \
  -p "${PORT}:8080" \
  -p 50000:50000 \
  bazel/jenkins:jenkins-test >/dev/null

test_http() {
  return [[ "$(curl -sI "$1")" =~ ^HTTP/[0-9.]+\ 2 ]]
}

# Wait for jenkins to start-up for at most 3 minutes
echo -n "*** Waiting for jenkins server to be up and running"
timeout=180
ts="$(date +%s)"
while ! [[ "$(curl -sI  "http://$DOCKER_SERVER:${PORT}/jnlpJars/slave.jar")" =~ ^HTTP/[0-9.]+\ 2 ]]
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

# Run the executor nodes, in priviledged mode for Bazel.
container1="$(docker run -d --privileged=true \
                --link jenkins:jenkins --env JENKINS_SERVER=http://jenkins:${PORT} \
                bazel/jenkins:ubuntu-docker.docker)"
container2="$(docker run -d --privileged=true \
                --link jenkins:jenkins --env JENKINS_SERVER=http://jenkins:${PORT} \
                bazel/jenkins:deploy.docker)"

# Connect to the master container, until the user quit.
docker attach jenkins

# Kill the executor nodes and remove containers.
docker rm -f "${container1}" > /dev/null
docker rm -f "${container2}" > /dev/null
docker rm -f jenkins > /dev/null
