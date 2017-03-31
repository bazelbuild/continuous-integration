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

# Android support

set -eu

# NDK
mkdir -p /home/ci/android
cd /home/ci/android
curl -o android-ndk.bin http://dl.google.com/android/ndk/android-ndk-r10e-linux-x86_64.bin
chmod +x android-ndk.bin
./android-ndk.bin >/dev/null
rm android-ndk.bin

# Android SDK
mkdir -p /home/ci/android/android-sdk-linux
cd /home/ci/android/android-sdk-linux
curl -o tools.zip https://dl.google.com/android/repository/tools_r25.2.3-linux.zip
unzip tools.zip
rm tools.zip
expect -c '
set timeout -1;
spawn /home/ci/android/android-sdk-linux/tools/bin/sdkmanager --update
expect {
    "Accept? (y/N)" { exp_send "y\r" ; exp_continue }
    eof
}
'
tools/bin/sdkmanager "platforms;android-24" "platform-tools" "build-tools;24.0.3" "add-ons;addon-google_apis-google-24" "extras;android;m2repository"
chown -R ci /home/ci/android
