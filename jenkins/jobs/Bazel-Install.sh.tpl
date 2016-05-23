#!/bin/bash
# Copyright 2016 The Bazel Authors. All rights reserved.
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

# Shell script to install bazel on the host

set -eux

# Get the platform we are running on
PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m)

# Create the URL to download a specific version of bazel for current platform
create_url() {
  local version="$1"
  local flavour="${2-}"
  if [ -n "${flavour}" ]; then
    flavour="-${2}"
  fi
  echo "https://github.com/bazelbuild/bazel/releases/download/${version}/bazel-${version}${flavour}-installer-${PLATFORM}.sh"
}

# Install bazel using the specified installer
install_bazel() {
  local installer="$1"
  local destination="$2"
  mkdir -p "${destination}"
  if [[ "${installer}" =~ ^https?:// ]]; then
    curl -L -o install.sh "${installer}"
    installer="${PWD}/install.sh"
  fi
  chmod 0755 "${installer}"
  rm -fr "${destination}"
  "${installer}" \
    --base="${destination}" \
    --bin="${destination}/binary"
}

# Get the version of latest BAZEL
if [ -z "${BAZEL_VERSION:-}" ]; then
  BAZEL_VERSION=$(curl -I https://github.com/bazelbuild/bazel/releases/latest | grep '^Location: ' | sed 's|.*/||' | sed $'s/\r//')
fi

# Install bazel from HEAD
install_bazel "$(find $PWD/bazel-installer -name '*.sh' | \
  grep -F "PLATFORM_NAME=${PLATFORM}" | grep -Fv jdk7 | head -1)" \
  ~/.bazel/HEAD
install_bazel "$(find $PWD/bazel-installer -name '*.sh' | \
  grep -F "PLATFORM_NAME=${PLATFORM}" | grep -F jdk7 | head -1)" \
  ~/.bazel/HEAD-jdk7

# Install latest Bazel if not yet installed
if [ ! -d ~/.bazel/${BAZEL_VERSION} ]; then
  install_bazel "$(create_url ${BAZEL_VERSION})" \
    ~/.bazel/${BAZEL_VERSION}
fi
if [ ! -d ~/.bazel/${BAZEL_VERSION}-jdk7 ]; then
  install_bazel "$(create_url ${BAZEL_VERSION} "jdk7")" \
    ~/.bazel/${BAZEL_VERSION}-jdk7
fi

# Recreate symlinks to the latest version for Bazel
rm -f ~/.bazel/latest ~/.bazel/latest-jdk7
ln -s ~/.bazel/${BAZEL_VERSION} ~/.bazel/latest
ln -s ~/.bazel/${BAZEL_VERSION}-jdk7 ~/.bazel/latest-jdk7
