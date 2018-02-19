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

set -eu

# Use a local SSD if available, otherwise use a RAM disk for our builds.
# if [ -e /dev/nvme0n1 ]; then
#   mkfs.ext4 -F /dev/nvme0n1
#   # TODO(philwo) add 'discard' option again, when b/68062163 is fixed.
#   mount -o defaults,nobarrier /dev/nvme0n1 /var/lib/buildkite-agent
#   chown -R buildkite-agent:buildkite-agent /var/lib/buildkite-agent
#   chmod 0755 /var/lib/buildkite-agent
#   mkdir /var/lib/buildkite-agent/docker
#   chown root:root /var/lib/buildkite-agent/docker
#   chmod 0711 /var/lib/buildkite-agent/docker
# fi

# Use the local SSD as swap space.
if [ -e /dev/nvme0n1 ]; then
  mkswap -f /dev/nvme0n1
  swapon /dev/nvme0n1
fi

# Make /tmp a tmpfs.
mount -t tmpfs -o mode=1777,uid=root,gid=root tmpfs /tmp
mount -t tmpfs -o mode=0711,uid=root,gid=root tmpfs /var/lib/docker
mount -t tmpfs -o mode=0755,uid=buildkite-agent,gid=buildkite-agent tmpfs /var/lib/buildkite-agent

# Start Docker.
if [[ -e /bin/systemctl ]]; then
  systemctl start docker
else
  service docker start
fi

# Get the Buildkite Token from GCS and decrypt it using KMS.
BUILDKITE_TOKEN=$(curl -sS "https://storage.googleapis.com/bazel-encrypted-secrets/buildkite-agent-token.enc" | \
  gcloud kms decrypt --location global --keyring buildkite --key buildkite-agent-token --ciphertext-file - --plaintext-file -)

# Insert the Buildkite Token into the agent configuration.
sed -i "s/token=\"xxx\"/token=\"${BUILDKITE_TOKEN}\"/" /etc/buildkite-agent/buildkite-agent.cfg

# Only start the Buildkite Agent if this is a worker node (as opposed to a VM
# being used by someone for testing / development).
if [[ $(hostname) == buildkite* ]]; then
  if [[ -e /bin/systemctl ]]; then
    systemctl start buildkite-agent
  else
    service buildkite-agent start
  fi
fi

exit 0
