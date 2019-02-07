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
#   origin direction destination local-name
# where
#   direction can be ==> or <=>
REPOSITORIES=(
    "https://bazel.googlesource.com/bazel ==> git@github.com:bazelbuild/bazel.git bazel"
    "https://bazel.googlesource.com/java_tools ==> git@github.com:bazelbuild/java_tools.git java_tools"
    "https://bazel.googlesource.com/rules_cc ==> git@github.com:bazelbuild/rules_cc.git rules_cc"
    "https://bazel.googlesource.com/tulsi ==> git@github.com:bazelbuild/tulsi.git tulsi"
)

set -euxo pipefail

# Download & decrypt gitcookies.
gsutil cat "gs://bazel-trusted-encrypted-secrets/gitsync-cookies.enc" | \
    gcloud kms decrypt --location "global" --keyring "buildkite" --key "gitsync-cookies-key" --plaintext-file "-" --ciphertext-file "-" \
    > /home/gitsync/.gitcookies
chmod 0600 /home/gitsync/.gitcookies

# Download & decrypt GitHub SSH key.
gsutil cat "gs://bazel-trusted-encrypted-secrets/gitsync-ssh.enc" | \
    gcloud kms decrypt --location "global" --keyring "buildkite" --key "gitsync-ssh-key" --plaintext-file "-" --ciphertext-file "-" \
    > /home/gitsync/.ssh/id_rsa
chmod 0600 /home/gitsync/.ssh/id_rsa

function clone() {
  local origin="$1"
  local destination="$3"
  local name="$4"

  rm -rf "${name}"
  git clone "${origin}" "${name}"
  pushd "${name}"
  git remote add destination "${destination}"
  popd
}

function sync() {
  local origin="$1"
  local direction="$2"
  local destination="$3"
  local name="$4"

  pushd "${name}"
  echo "Syncing ${origin} ${direction} ${destination} ..."
  git remote update --prune
  git checkout "origin/master" -B "master"
  if [[ "${direction}" == "<=>" ]]; then
    git rebase "destination/master"
    git push -f origin master
  fi
  git push destination master
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
