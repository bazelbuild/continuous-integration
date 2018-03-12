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

# If available: Use a persistent disk as a use-case specific data volume.
if [[ -e /dev/sdb ]]; then
  if [[ ! -e /dev/vg0 ]]; then
    pvcreate /dev/sdb
    vgcreate vg0 /dev/sdb
  fi

  if [[ $(hostname) == *testing* ]]; then
    # On "testing" machines, we create big /var/lib/docker and /home directories so that everyone
    # has enough space to try out stuff.
    if [[ ! -e /dev/vg0/docker ]]; then
      lvcreate -n docker -l25%FREE vg0
      mkfs.ext4 /dev/vg0/docker
    fi
    mount /dev/vg0/docker /var/lib/docker
    chmod 0711 /var/lib/docker

    if [[ ! -e /dev/vg0/home ]]; then
      lvcreate -n home -l100%FREE vg0
      mkfs.ext4 /dev/vg0/home
    fi
    mkdir /tmp/home
    rsync -a /home/ /tmp/home/
    mount /dev/vg0/home /home
    rsync -a /tmp/home/ /home/
    rm -rf /tmp/home
  elif [[ $(hostname) == *pipeline* ]]; then
    # On "pipeline" machines, we create a big /var/lib/buildkite-agent directory, because these
    # machines check out a lot of different Git repositories.
    if [[ ! -e /dev/vg0/buildkite-agent ]]; then
      lvcreate -n buildkite-agent -l100%FREE vg0
      mkfs.ext4 /dev/vg0/buildkite-agent
    fi
    mount /dev/vg0/buildkite-agent /var/lib/buildkite-agent
    chown -R buildkite-agent:buildkite-agent /var/lib/buildkite-agent
  fi
fi

# If available: Use the local SSD as swap space.
if [[ -e /dev/nvme0n1 ]]; then
  mkswap -f /dev/nvme0n1
  swapon /dev/nvme0n1

  # Move fast and lose data.
  mount -t tmpfs -o mode=1777,uid=root,gid=root,size=$((100 * 1024 * 1024 * 1024)) tmpfs /tmp
  mount -t tmpfs -o mode=0711,uid=root,gid=root,size=$((100 * 1024 * 1024 * 1024)) tmpfs /var/lib/docker
  mount -t tmpfs -o mode=0755,uid=buildkite-agent,gid=buildkite-agent,size=$((100 * 1024 * 1024 * 1024)) tmpfs /var/lib/buildkite-agent
fi

# Start Docker if it's installed.
if [[ $(docker --version 2>/dev/null) ]]; then
  if [[ $(systemctl --version 2>/dev/null) ]]; then
    systemctl start docker
  else
    service docker start
  fi
fi

# Only start the Buildkite Agent if this is a worker node (as opposed to a VM
# being used by someone for testing / development).
if [[ $(hostname) == buildkite* ]]; then
  # Get the Buildkite Token from GCS and decrypt it using KMS.
  BUILDKITE_TOKEN=$(curl -sS "https://storage.googleapis.com/bazel-encrypted-secrets/buildkite-agent-token.enc" | \
    gcloud kms decrypt --location global --keyring buildkite --key buildkite-agent-token --ciphertext-file - --plaintext-file -)

  # Insert the Buildkite Token into the agent configuration.
  sed -i "s/token=\"xxx\"/token=\"${BUILDKITE_TOKEN}\"/" /etc/buildkite-agent/buildkite-agent.cfg

  if [[ $(hostname) == *pipeline* ]]; then
    # Start 8 instances of the Buildkite agent.
    for i in $(seq 8); do
      systemctl start buildkite-agent@$i
    done
  elif [[ -e /bin/systemctl ]]; then
    systemctl start buildkite-agent
  else
    service buildkite-agent start
  fi
fi

exit 0
