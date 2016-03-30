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

# Scripts to configure the service that will poll git repositories for
# in sync check.

# Format of each entry is:
#   origin destination local-name branch1 ... branchN
REPOSITORIES=(
    "https://bazel.googlesource.com/bazel git@github.com:bazelbuild/bazel.git bazel master gh-pages"
    "https://bazel.googlesource.com/continuous-integration git@github.com:bazelbuild/continuous-integration.git continuous-integration master"
    "https://bazel.googlesource.com/skydoc git@github.com:bazelbuild/skydoc.git master"
)

# Install certificates
(cd /usr/share/ca-certificates && find -type f -name '*.crt' \
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

set -eux

cd /tmp

function clone() {
  git clone $1 $3
  pushd $3
  git remote add destination $2
  popd
}

function sync() {
  pushd $3
  shift 3
  git fetch origin
  git fetch destination
  for branch in "$@"; do
    git checkout origin/${branch} -B ${branch} && git push destination ${branch}
  done
  popd
}

# Get a local clone
for i in "${REPOSITORIES[@]}"; do
  clone $i
done

# Sync loop
while true; do
  for i in "${REPOSITORIES[@]}"; do
    sync $i
  done
  # Sleep 30 seconds between each sync
  sleep 30
done
