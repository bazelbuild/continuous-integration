#!/bin/bash
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

set -eu

# Configure the service
cat >launch.sh <<'EOF'
#!/bin/bash

cd $HOME

retry=1
while (( $retry != 0 )); do
  retry=0
  rm -f slave.jar
  curl -qo slave.jar http://master.ci.bazel.io/jnlpJars/slave.jar || retry=1
  sleep 5
done

export ANDROID_SDK_PATH=$(echo $HOME/android-sdk-*)
export ANDROID_NDK_PATH=$(echo $HOME/android-ndk-*)
export ANDROID_SDK_BUILD_TOOLS_VERSION=$(ls $ANDROID_SDK_PATH/build-tools | sort -n | tail -1)
export ANDROID_SDK_API_LEVEL=$(ls $ANDROID_SDK_PATH/platforms | cut -d '-' -f 2 | sort -n | tail -1)
export ANDROID_NDK_API_LEVEL=$(ls $ANDROID_NDK_PATH/platforms | cut -d '-' -f 2 | sort -n | tail -1)
export PATH=/Users/ci/node/node-v6.9.1-darwin-x64/bin:$PATH

while true; do
  $(which java) -jar slave.jar -jnlpUrl https://ci.bazel.build/computer/$(cat $HOME/node_name)/slave-agent.jnlp -noReconnect
  # Something went wrong. Sleep and retry in 1 minute.
  sleep 60
done
EOF
chmod +x launch.sh

cat <<EOF | sudo tee /Library/LaunchDaemons/jenkins.plist
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0 //EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>io.bazel.ci.jenkins.slave</string>
    <key>ProgramArguments</key>
    <array></array>
    <key>UserName</key>
    <string>$USER</string>
    <key>Program</key>
    <string>$HOME/launch.sh</string>
    <key>StandardOutputPath</key>
    <string>$HOME/jenkins.slave.out.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/jenkins.slave.err.log</string>
    <key>KeepAlive</key>
    <true/>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
EOF

sudo launchctl load /Library/LaunchDaemons/jenkins.plist
