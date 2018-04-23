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

# Android NDK
cd /opt
curl -sSLo android-ndk.zip https://dl.google.com/android/repository/android-ndk-r15c-linux-x86_64.zip
unzip android-ndk.zip > /dev/null
rm android-ndk.zip

# Android SDK
mkdir -p /opt/android-sdk-linux
cd /opt/android-sdk-linux
curl -sSLo android-sdk.zip https://dl.google.com/android/repository/sdk-tools-linux-3859397.zip
unzip android-sdk.zip > /dev/null
rm android-sdk.zip
expect -c '
set timeout -1
log_user 0
spawn tools/bin/sdkmanager --update
expect {
    "Accept? (y/N)" { exp_send "y\r" ; exp_continue }
    eof
}
'

# This should be kept in sync with mac/mac-android.sh.
tools/bin/sdkmanager \
  "build-tools;27.0.3" \
  "emulator" \
  "extras;android;m2repository" \
  "platform-tools" \
  "platforms;android-24" \
  "platforms;android-25" \
  "platforms;android-26" \
  "platforms;android-27" \
  "system-images;android-19;default;x86" \
  "system-images;android-21;default;x86" \
  "system-images;android-22;default;x86" \
  "system-images;android-23;default;x86" \
  > /dev/null
chown -R root:root /opt/android*
