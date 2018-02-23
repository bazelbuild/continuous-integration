#!/bin/bash
#
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

# Setup script for Ubuntu 14.04 LTS and 16.04 LTS.

# Prevent dpkg / apt-get / debconf from trying to access stdin.
export DEBIAN_FRONTEND=noninteractive

# Android SDK requires 32-bits libraries.
dpkg --add-architecture i386

apt-get -qqy update > /dev/null
apt-get -qqy dist-upgrade > /dev/null

packages=(
  # Bazel dependencies.
  build-essential
  clang
  curl
  git
  python
  python-dev
  python-mock
  python-numpy
  python-pip
  python3
  python3-dev
  python3-mock
  python3-numpy
  python3-pip
  realpath
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
  swig
)
apt-get -qqy install "${packages[@]}" > /dev/null
