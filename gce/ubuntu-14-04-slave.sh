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

# Setup scripts for Ubuntu 14.04

echo y | add-apt-repository ppa:webupd8team/java
apt-get update
apt-get install -y zip g++ zlib1g-dev wget git unzip python python3 curl realpath xvfb

# Should accept the licence:
yes | apt-get install -y oracle-java8-installer

# Android SDK requires 32-bits libraries
sudo dpkg --add-architecture i386
sudo apt-get -qqy update
sudo apt-get -qqy install libncurses5:i386 libstdc++6:i386 zlib1g:i386
sudo apt-get -y install expect  # Needed to 'yes' the SDK licenses.

# Dependencies for TensorFlow
sudo apt-get -y install python-numpy swig python-dev python-pip libcurl3-dev
sudo pip install mock
