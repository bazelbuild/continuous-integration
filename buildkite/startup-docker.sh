#!/bin/bash
#
# Copyright 2018 The Bazel Authors. All rights reserved.
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

# Fail on errors.
# Fail when using undefined variables.
# Print all executed commands.
# Fail when any command in a pipe fails.
set -euxo pipefail

# Wait for all snaps to become available.
snap wait system seed.loaded

# Prevent dpkg / apt-get / debconf from trying to access stdin.
export DEBIAN_FRONTEND="noninteractive"

# Ubuntu 18.04 installs gcloud, gsutil, etc. commands in /snap/bin
export PATH=$PATH:/snap/bin:/snap/google-cloud-sdk/current/bin

# Optimize the CPU scheduler for throughput.
# (see https://unix.stackexchange.com/questions/466722/how-to-change-the-length-of-time-slices-used-by-the-linux-cpu-scheduler/466723)
sysctl -w kernel.sched_min_granularity_ns=10000000
sysctl -w kernel.sched_wakeup_granularity_ns=15000000
sysctl -w vm.dirty_ratio=40
#echo always > /sys/kernel/mm/transparent_hugepage/enabled

# Fix permissions of /dev/kvm.
chmod -v 0666 /dev/kvm

# Use the local SSDs as fast storage for Docker and the Buildkite agent.
zpool destroy -f bazel || true
zpool create -f \
    -o ashift=12 \
    -O canmount=off \
    -O compression=lz4 \
    -O normalization=formD \
    -O relatime=on \
    -O sync=disabled \
    -O xattr=sa \
    bazel /dev/nvme0n?

rm -rf /var/lib/bazelbuild
zfs create -o mountpoint=/var/lib/bazelbuild bazel/bazelbuild
curl https://storage.googleapis.com/bazel-git-mirror/bazelbuild.tar | tar x -C /var/lib
chown -R root:root /var/lib/bazelbuild
chmod -R 0755 /var/lib/bazelbuild

rm -rf /var/lib/buildkite-agent
zfs create -o mountpoint=/var/lib/buildkite-agent bazel/buildkite-agent
chown buildkite-agent:buildkite-agent /var/lib/buildkite-agent
chmod 0755 /var/lib/buildkite-agent

rm -rf /var/lib/docker
zfs create -o mountpoint=/var/lib/docker bazel/docker
chown root:root /var/lib/docker
chmod 0711 /var/lib/docker

# Configure and start Docker.
cat > /etc/docker/daemon.json <<'EOF'
{
  "insecure-registries" : ["docker-cache.europe-north1-a.c.bazel-untrusted.internal:5000"],
  "storage-driver": "zfs"
}
EOF
systemctl start docker

# Pull some known images so that we don't have to download / extract them on each CI job.
gcloud auth configure-docker --quiet
docker pull gcr.io/bazel-untrusted/ubuntu1404:java8 &
docker pull gcr.io/bazel-untrusted/ubuntu1604:java8 &
for java in java8 java9 java10 nojava; do
  docker pull gcr.io/bazel-untrusted/ubuntu1804:$java &
done
wait

# Get the Buildkite Token from GCS and decrypt it using KMS.
BUILDKITE_TOKEN=$(gsutil cat "gs://bazel-untrusted-encrypted-secrets/buildkite-untrusted-agent-token.enc" | \
  gcloud kms decrypt --project bazel-untrusted --location global --keyring buildkite --key buildkite-untrusted-agent-token --ciphertext-file - --plaintext-file -)

# Write the Buildkite agent configuration.
cat > /etc/buildkite-agent/buildkite-agent.cfg <<EOF
token="${BUILDKITE_TOKEN}"
name="%hostname"
tags="kind=docker,os=linux"
build-path="/var/lib/buildkite-agent/builds"
hooks-path="/etc/buildkite-agent/hooks"
plugins-path="/etc/buildkite-agent/plugins"
git-clone-flags="-v --reference /var/lib/bazelbuild"
EOF

# Add the Buildkite agent hooks.
cat > /etc/buildkite-agent/hooks/environment <<'EOF'
#!/bin/bash

set -euo pipefail

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin:/snap/google-cloud-sdk/current/bin"
export BUILDKITE_ARTIFACT_UPLOAD_DESTINATION="gs://bazel-untrusted-buildkite-artifacts/$BUILDKITE_JOB_ID"
export BUILDKITE_GS_ACL="publicRead"
EOF

# Fix permissions of the Buildkite agent configuration files and hooks.
chmod 0400 /etc/buildkite-agent/buildkite-agent.cfg
chmod 0500 /etc/buildkite-agent/hooks/*
chown -R buildkite-agent:buildkite-agent /etc/buildkite-agent

# Start the Buildkite agent service.
systemctl start buildkite-agent

exit 0
