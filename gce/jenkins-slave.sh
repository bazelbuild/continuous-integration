#!/bin/sh
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

cat > /root/jenkins-startup <<'EOF'
&> /root/jenkins-startup.log

# Wait until the machine is set-up on creation.
while ! (id ci >&/dev/null) || [ ! -f /home/ci/node_name ]; do
  sleep 60
done

# Reboot if required, before going into operation.
if [ -f /var/run/reboot-required ]; then
  reboot
fi

NODE_NAME=$(cat /home/ci/node_name)

# Setup NodeJS (only on Linux).
if [[ ! -d /home/ci/node && $(uname) == "Linux" ]]; then
  mkdir -p /home/ci/node &&
  cd /home/ci/node &&
  curl https://nodejs.org/dist/v8.9.4/node-v8.9.4-linux-x64.tar.xz | tar xJ &&
  PATH=/home/ci/node/node-v8.9.4-linux-x64/bin:$PATH npm install -g typescript fried-twinkie
fi

cd /home/ci

# Setup the various Android SDK paths.
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

# Keep the agent running, even if it crashes or the server is temporarily not available.
while true; do
  wget -O slave.jar https://ci.bazel.build/jnlpJars/slave.jar &&
  sudo -u ci \
      ANDROID_SDK_PATH=$ANDROID_SDK_PATH \
      ANDROID_SDK_BUILD_TOOLS_VERSION=$ANDROID_SDK_BUILD_TOOLS_VERSION \
      ANDROID_SDK_API_LEVEL=$ANDROID_SDK_API_LEVEL \
      ANDROID_NDK_PATH=$ANDROID_NDK_PATH \
      ANDROID_NDK_API_LEVEL=$ANDROID_NDK_API_LEVEL \
      PATH=/home/ci/node/node-v8.9.4-linux-x64/bin:$PATH \
      $(which java) -jar slave.jar -jnlpUrl https://ci.bazel.build/computer/${NODE_NAME}/slave-agent.jnlp -noReconnect

  # Something went wrong. Sleep and retry in 1 minute.
  sleep 60
done

EOF

# As this init script is called before the setup is complete, we have to do
# some dance to make sure we only start the actual script once bash (optional
# on some systems) is installed.

cat > /root/call-jenkins-startup <<'EOF'
PATH=$PATH:/usr/local/bin ; export PATH
echo `date` PATH=$PATH >> /root/early-startup.log

while [ -z "`which bash`" ] ; do
  echo `date` Waiting for bash to be installed >> /root/early-startup.log
  sleep 60
done

bash /root/jenkins-startup
EOF

# Start the actual jenkins daemon
echo /bin/sh /root/call-jenkins-startup | batch
