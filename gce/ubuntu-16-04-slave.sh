# Copyright 2017 The Bazel Authors. All rights reserved.
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

# Setup scripts for Ubuntu 16.04.

# Android SDK requires 32-bits libraries.
dpkg --add-architecture i386
apt-get -y update
apt-get -y dist-upgrade

# Explicitly install the OpenJDK 8 before anything else to prevent
# Ubuntu from pulling in OpenJDK 9.
apt-get -y install \
  openjdk-8-jdk \
  openjdk-8-source

packages=(
  # Bazel dependencies.
  build-essential
  curl
  git
  python
  python3
  unzip
  wget
  xvfb
  zip
  zlib1g-dev

  # Dependencies for Android SDK.
  # https://developer.android.com/studio/troubleshoot.html#linux-libraries
  # https://code.google.com/p/android/issues/detail?id=207212
  expect
  libbz2-1.0:i386
  libncurses5:i386
  libstdc++6:i386
  libz1:i386

  # Dependencies for TensorFlow.
  libcurl3-dev
  python-dev
  python-numpy
  python-pip
  python-wheel
  swig
)
apt-get -y install "${packages[@]}"

pip install mock
