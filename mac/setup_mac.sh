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

# Command-line parameters
if [ ! $# -eq 1 ]; then
  echo "Usage: setup_mac.sh <nodename>"
  exit 1
fi
node_name=$1

# Test that we can sudo
if ! sudo /usr/bin/true; then
  echo "The CI user must have sudo right"
  exit
fi

cd $HOME

# Write the node name
echo -n ${node_name} > $HOME/node_name

# Try to accept Xcode license
sudo git version

# Set the machine to never sleep
sudo systemsetup -setcomputersleep Never

# Url to fetch other scripts
# We use script from HEAD, ideally we would use the same commit hash
# than this script but it is not really easy and we generally do not
# want to run that script from something else than HEAD.
MAC_SETUP_BASE_URL="${MAC_SETUP_BASE_URL-https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/}"

# Install Bazel
curl "${MAC_SETUP_BASE_URL}/gce/bootstrap-bazel.sh" | bash

# Install Android SDK
curl "${MAC_SETUP_BASE_URL}/mac/mac-android.sh" | bash

# Install the service
curl "${MAC_SETUP_BASE_URL}/mac/mac-service.sh" | bash
