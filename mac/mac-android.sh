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
#
# Before running this script install the JDK 8 and Xcode. Launch this script
# as the "ci" user.
#
# You should answer yes to all license requests and type your password
# when requested.

set -eu

# Install the Android NDK
curl -so android-ndk.zip https://dl.google.com/android/repository/android-ndk-r11c-darwin-x86_64.zip
unzip android-ndk.zip
rm android-ndk.zip

# Install the Android SDK
mkdir -p ~/android-sdk-macosx
cd ~/android-sdk-macosx
curl -o tools.zip https://dl.google.com/android/repository/sdk-tools-darwin-3859397.zip
unzip tools.zip
rm tools.zip
expect -c '
set timeout -1;
spawn /Users/ci/android-sdk-macosx/tools/bin/sdkmanager --update
expect {
    "Accept? (y/N)" { exp_send "y\r" ; exp_continue }
    eof
}
'
tools/bin/sdkmanager "platforms;android-24" "platform-tools" \
  "build-tools;24.0.3;" "build-tools;26.0.1" \
  "add-ons;addon-google_apis-google-24" "extras;android;m2repository"
