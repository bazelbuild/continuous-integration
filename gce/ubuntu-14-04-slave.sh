#!/bin/bash
#
# Copyright 2015 Google Inc. All rights reserved.
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

# Startup script to configure the ubuntu slave. As Bazel tests need
# a lot of memory, CPU and disk, we use a standalone VM instead of
# a docker image.

echo y | add-apt-repository ppa:webupd8team/java
apt-get update
apt-get install -y zip g++ zlib1g-dev wget git \ 
  unzip python python3 curl
# TODO(dmarting): Find a way to do that without someone to accept
# the licence:
# apt-get install -y oracle-java8-installer

# Create the Jenkins user
adduser --system --home /home/ci --uid 5000 ci
cd /home/ci

# Download dependencies
# The server might not be started yet, so do that in a loop until the server is up
# and running
retry=1
while (( $retry != 0 )); do
  retry=0
  rm -f slave.jar slave-agent.jnlp
  wget -nc http://jenkins/jnlpJars/slave.jar || retry=1
  wget -nc http://jenkins/computer/ubuntu_14.04-x86_64/slave-agent.jnlp || retry=1
  sleep 5
done

chmod a+r slave-agent.jnlp
sed -i.bak -E "s|http://ci\.bazel\.io/|http://jenkins/|g" slave-agent.jnlp

while true; do
  sudo -u ci $(which java) -jar slave.jar -jnlpUrl file:///home/ci/slave-agent.jnlp -noReconnect
  # The jenkins server is down, sleep and retries in 1 minute
  sleep 60
done
