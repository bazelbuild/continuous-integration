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

# Script to configure a mac machine.
# Before running this script install the JDK 8 and Xcode. Launch this script
# as the "ci" user.
# You should answer yes to all license requests and type your password
# when requested.

# Try to accept Xcode license
sudo git

# Write the node name
echo -n ${1:-darwin-x86_64} >$HOME/node_name

# Get the various sdk
cd $HOME
# Android NDK
curl -so android-ndk.bin http://dl.google.com/android/ndk/android-ndk-r10e-darwin-x86_64.bin
chmod +x android-ndk.bin
./android-ndk.bin
# Android SDK
curl -so android-sdk.zip http://dl.google.com/android/android-sdk_r24.3.4-macosx.zip
unzip android-sdk.zip
(cd android-sdk-macosx && tools/android update sdk --no-ui)

# Now configure the service
cat >launch.sh <<'EOF'
#!/bin/bash

cd $HOME
retry=1
while (( $retry != 0 )); do
  retry=0
  rm -f slave.jar slave-agent.jnlp
  curl -qo slave.jar http://ci.bazel.io/jnlpJars/slave.jar || retry=1
  curl -qo slave-agent.jnlp http://ci.bazel.io/computer/$(cat $HOME/node_name)/slave-agent.jnlp || retry=1
  sleep 5
done

export ANDROID_SDK_PATH=$(echo $HOME/android-sdk-*)
export ANDROID_NDK_PATH=$(echo $HOME/android-ndk-*)
export ANDROID_SDK_BUILD_TOOLS_VERSION=$(ls $ANDROID_SDK_PATH/build-tools | sort -n | tail -1)
export ANDROID_SDK_API_LEVEL=$(ls $ANDROID_SDK_PATH/platforms | cut -d '-' -f 2 | sort -n | tail -1)
export ANDROID_NDK_API_LEVEL=$(ls $ANDROID_NDK_PATH/platforms | cut -d '-' -f 2 | sort -n | tail -1)
chmod a+r slave-agent.jnlp

while true; do
  $(which java) -jar slave.jar -jnlpUrl file:///$HOME/slave-agent.jnlp -noReconnect
  # The jenkins server is probably down, sleep and retry in 1 minute
  sleep 60
done
EOF
chmod +x launch.sh

sudo cat >/System/Library/LaunchDaemons/jenkins.plist <<EOF
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

launchctl load /System/Library/LaunchDaemons/jenkins.plist
