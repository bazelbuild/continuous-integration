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

# Android support
# NDK
mkdir -p /home/ci/android
cd /home/ci/android
curl -o android-ndk.bin http://dl.google.com/android/ndk/android-ndk-r10e-linux-x86_64.bin
chmod +x android-ndk.bin
./android-ndk.bin >/dev/null
# Android SDK
curl -o android-sdk.tgz http://dl.google.com/android/android-sdk_r24.3.4-linux.tgz
tar zxf android-sdk.tgz
(cd android-sdk-linux && tools/android update sdk --no-ui)

