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
#   origin destination local-name bidirectional branch1 ... branchN
REPOSITORIES=(
    "https://bazel.googlesource.com/bazel git@github.com:bazelbuild/bazel.git bazel false master"
    "https://bazel.googlesource.com/tulsi git@github.com:bazelbuild/tulsi.git tulsi false master"
    "https://bazel.googlesource.com/continuous-integration git@github.com:bazelbuild/continuous-integration.git continuous-integration true master"
    "https://bazel.googlesource.com/devtools git@github.com:bazelbuild/devtools.git devtools false master"
    "https://bazel.googlesource.com/eclipse git@github.com:bazelbuild/eclipse.git eclipse true master"
    "https://bazel.googlesource.com/bazel-toolchains git@github.com:bazelbuild/bazel-toolchains.git bazel-toolchains false master"
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

set -eu

cd /tmp

function log() {
  echo "[$(date -u '+%Y-%m-%d %H:%M:%S')] $*"
}

function clone() {
  git clone $1 $3
  pushd $3
  git remote add destination $2
  popd
}

function sync_branch() {
  log "sync_branch $*"
  local branch="$1"
  local bidirectional="$2"
  git checkout origin/${branch} -B ${branch} || {
    echo "Failed to checkout ${branch}, aborting sync..."
    return 1
  }

  log "Origin branch is $(git rev-parse origin/master), destination is $(git rev-parse destination/master)"
  if $bidirectional; then
    git rebase destination/${branch} || {
      echo "Failed to rebase ${branch} from destination, aborting sync..."
      git rebase --abort &>/dev/null || true
      return 1
    }
    git push -f origin ${branch} || {
      echo "Failed to force pushed to origin, aborting sync..."
      return 1
    }
  fi

  log "New head for destination is $(git rev-parse HEAD)"
  git push destination ${branch} || {
    echo "Failed to push to destination..."
    return 1
  }
}

function sync() {
  log "sync $*"
  local bidirectional="$4"
  pushd $3
  shift 4
  git fetch origin
  git fetch destination
  for branch in "$@"; do
    sync_branch "${branch}" "${bidirectional}" || true
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
