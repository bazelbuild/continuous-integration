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

# Scripts to configure the service that will check that all external bazel
# dependencies are properly mirrored on GCS.

# Format of each entry is:
#   repository (it should work with git clone ...
#   directory
#   workspace file
REPOSITORIES=(
    "https://tensorflow.googlesource.com/staging staging tensorflow/workspace.bzl"
    "git@github.com:tensorflow/tensorflow.git tensorflow tensorflow/workspace.bzl"
)

# Install certificates
(cd /usr/share/ca-certificates && find . -type f -name '*.crt' \
    | sed -e 's|^\./||') > /etc/ca-certificates.conf
update-ca-certificates

# Set-up deploy keys
mkdir -p ~/.ssh
cat >~/.ssh/config <<'EOF'
Host               github.com
    Hostname       github.com
    User           git
    IdentityFile   /opt/secrets/github_id_rsa
    IdentitiesOnly yes
    StrictHostKeyChecking no
EOF

git config --global http.cookiefile /opt/secrets/gerritcookies

set -eux

# Setup tmp folder for our use and cd into it.
cp check_bazel_deps.py /tmp/check_bazel_deps.py
cd /tmp

# Setup gsutil
wget https://storage.googleapis.com/pub/gsutil.tar.gz
tar zxf gsutil.tar.gz

function clone() {
  git clone $1
}

function mirror() {
  pushd ${2}
  git pull
  popd

  python check_bazel_deps.py ${2}/${3}
}

# Get a local clone
for i in "${REPOSITORIES[@]}"; do
  clone $i
done

# Sync loop
while true; do
  for i in "${REPOSITORIES[@]}"; do
    mirror $i
  done
  # Sleep 600 seconds between each sync
  sleep 600
done
