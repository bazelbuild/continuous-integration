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

set -euxo pipefail

# Ubuntu 18.04 installs gcloud, gsutil, etc. commands in /snap/bin
PATH=$PATH:/snap/bin

until command -v gsutil &>/dev/null; do
  echo "Waiting for gsutil / gcloud to become available..."
  sleep 1
done

# If available: Use the local SSD as swap space.
if [[ -e /dev/nvme0n1 ]]; then
  mkswap -f /dev/nvme0n1
  swapon /dev/nvme0n1

  # Move fast and lose data.
  mount -t tmpfs -o mode=1777,uid=root,gid=root,size=$((100 * 1024 * 1024 * 1024)) tmpfs /tmp
  mount -t tmpfs -o mode=0711,uid=root,gid=root,size=$((100 * 1024 * 1024 * 1024)) tmpfs /var/lib/docker
  mount -t tmpfs -o mode=0755,uid=buildkite-agent,gid=buildkite-agent,size=$((100 * 1024 * 1024 * 1024)) tmpfs /var/lib/buildkite-agent
fi

# Start Docker.
if [[ $(systemctl --version 2>/dev/null) ]]; then
  systemctl start docker
else
  service docker start
fi

# Download a static bundle of all our Git repositories and unpack it.
rm -rf /var/lib/bazelbuild
curl -sS https://storage.googleapis.com/bazel-git-mirror/bazelbuild.tar | tar x -C /var/lib
chown -R root:root /var/lib/bazelbuild
chmod -R 0755 /var/lib/bazelbuild

# Get the Buildkite Token from GCS and decrypt it using KMS.
BUILDKITE_TOKEN=$(gsutil cat "gs://bazel-encrypted-secrets/buildkite-agent-token.enc" | \
  gcloud kms decrypt --location global --keyring buildkite --key buildkite-agent-token --ciphertext-file - --plaintext-file -)

# Insert the Buildkite Token into the agent configuration.
sed -i "s/token=\"xxx\"/token=\"${BUILDKITE_TOKEN}\"/" /etc/buildkite-agent/buildkite-agent.cfg
sed -i "s/name=.*/name=%hostname/" /etc/buildkite-agent/buildkite-agent.cfg

# Fix permissions of the Buildkite agent configuration files and hooks.
chmod 0400 /etc/buildkite-agent/buildkite-agent.cfg
chmod 0500 /etc/buildkite-agent/hooks/*
chown -R buildkite-agent:buildkite-agent /etc/buildkite-agent

# Start the Buildkite agent service.
if [[ $(hostname) == *pipeline* ]]; then
  # We run multiple agents on this machine, so append a counter to the name.
  sed -i "s/name=.*/name=%hostname-%n/" /etc/buildkite-agent/buildkite-agent.cfg

  # Start 8 instances of the Buildkite agent.
  for i in $(seq 8); do
    systemctl start buildkite-agent@$i
  done
elif [[ -e /bin/systemctl ]]; then
  systemctl start buildkite-agent
else
  service buildkite-agent start
fi

exit 0
