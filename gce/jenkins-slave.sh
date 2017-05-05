#!/usr/bin/env bash
#
# Copyright 2015 The Bazel Authors. All rights reserved.
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

# Startup script for our various *nix executor nodes.
# This is just setting up a slave to run.

# We ignore errors on this script as we want to retry on errors.

# Wait until the machine is set-up on creation
while ! (id ci >&/dev/null) || [ ! -f /home/ci/node_name ]; do
  sleep 60
done

# Reboot if required, before going into operation.
if [ -f /var/run/reboot-required ]; then
  reboot
fi

NODE_NAME=$(cat /home/ci/node_name)
MASTER=jenkins
if [[ "$NODE_NAME" =~ .*-staging$ ]]; then
  MASTER=jenkins-staging
fi

cd /home/ci
# Setup the various android paths
export ANDROID_SDK_PATH=$(echo /home/ci/android/android-sdk-*)
export ANDROID_NDK_PATH=$(echo /home/ci/android/android-ndk-*)
if [ -d "${ANDROID_SDK_PATH}" ]; then
  export ANDROID_SDK_BUILD_TOOLS_VERSION=$(ls $ANDROID_SDK_PATH/build-tools | sort -n | tail -1)
  export ANDROID_SDK_API_LEVEL=$(ls $ANDROID_SDK_PATH/platforms | cut -d '-' -f 2 | sort -n | tail -1)
else
  unset ANDROID_SDK_PATH
fi
if [ -d "${ANDROID_NDK_PATH}" ]; then
  export ANDROID_NDK_API_LEVEL=$(ls $ANDROID_NDK_PATH/platforms | cut -d '-' -f 2 | sort -n | tail -1)
else
  unset ANDROID_NDK_PATH
fi

# Download dependencies
# The server might not be started yet, so do that in a loop until the server is up
# and running
function get_slave_agent() {
  rm -f slave.jar slave-agent.jnlp
  wget -nc http://${MASTER}/jnlpJars/slave.jar || return 1
  wget -nc http://${MASTER}/computer/${NODE_NAME}/slave-agent.jnlp || return 1
  chmod a+r slave-agent.jnlp
  if [[ "$NODE_NAME" =~ .*-staging$ ]]; then
      sed -i.bak "s|http://ci-staging\.bazel\.io/|http://${MASTER}/|g" slave-agent.jnlp
  else
      sed -i.bak "s|http://ci\.bazel\.io/|http://${MASTER}/|g" slave-agent.jnlp
  fi
}

# Run jenkins slave agent
function run_agent() {
  sudo -u ci \
      ANDROID_SDK_PATH=$ANDROID_SDK_PATH \
      ANDROID_SDK_BUILD_TOOLS_VERSION=$ANDROID_SDK_BUILD_TOOLS_VERSION \
      ANDROID_SDK_API_LEVEL=$ANDROID_SDK_API_LEVEL \
      ANDROID_NDK_PATH=$ANDROID_NDK_PATH \
      ANDROID_NDK_API_LEVEL=$ANDROID_NDK_API_LEVEL \
      $(which java) -jar slave.jar -jnlpUrl file:///home/ci/slave-agent.jnlp -noReconnect
}

while true; do
  get_slave_agent && run_agent
  # The jenkins server is down, sleep and retries in 1 minute
  sleep 60
done
