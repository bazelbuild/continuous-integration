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
curl -o android-ndk.zip https://dl.google.com/android/repository/android-ndk-r14b-darwin-x86_64.zip
unzip android-ndk.zip
rm android-ndk.zip

# Install the Android SDK
mkdir -p ~/android-sdk-macosx
cd ~/android-sdk-macosx
curl -o android-sdk.zip https://dl.google.com/android/repository/sdk-tools-darwin-3859397.zip
unzip android-sdk.zip
rm android-sdk.zip
expect -c '
set timeout -1;
spawn tools/bin/sdkmanager --update
expect {
    "Accept? (y/N)" { exp_send "y\r" ; exp_continue }
    eof
}
'

# This should be kept in sync with linux/linux-android.sh
yes | tools/bin/sdkmanager \
  "platform-tools" \
  "build-tools;27.0.3" \
  "platforms;android-24" \
  "platforms;android-25" \
  "platforms;android-26" \
  "platforms;android-27" \
  "extras;android;m2repository"
