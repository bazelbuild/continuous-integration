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

# Use the local SSDs as fast storage.
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

# Create filesystem for Docker.
rm -rf /var/lib/docker
zfs create -o mountpoint=/var/lib/docker bazel/docker
chown root:root /var/lib/docker
chmod 0711 /var/lib/docker

mkdir /var/lib/docker/bazel-cache
chown buildkite-agent:buildkite-agent /var/lib/docker/bazel-cache
chmod 0755 /var/lib/docker/bazel-cache

# Get configuration parameters.
case $(hostname) in
  *trusted*)
    PROJECT="bazel-public"
    ARTIFACT_BUCKET="bazel-trusted-buildkite-artifacts"
    # Get the Buildkite Token from GCS and decrypt it using KMS.
    BUILDKITE_TOKEN=$(gsutil cat "gs://bazel-trusted-encrypted-secrets/buildkite-trusted-agent-token.enc" | \
        gcloud kms decrypt --project bazel-public --location global --keyring buildkite --key buildkite-trusted-agent-token --ciphertext-file - --plaintext-file -)
    ;;
  *)
    PROJECT="bazel-untrusted"
    ARTIFACT_BUCKET="bazel-untrusted-buildkite-artifacts"
    # Get the Buildkite Token from GCS and decrypt it using KMS.
    BUILDKITE_TOKEN=$(gsutil cat "gs://bazel-untrusted-encrypted-secrets/buildkite-untrusted-agent-token.enc" | \
        gcloud kms decrypt --project bazel-untrusted --location global --keyring buildkite --key buildkite-untrusted-agent-token --ciphertext-file - --plaintext-file -)
    ;;
esac

# Configure and start Docker.
cat > /etc/docker/daemon.json <<EOF
{
  "storage-driver": "zfs"
}
EOF
systemctl start docker

# Pull some known images so that we don't have to download / extract them on each CI job.
gcloud auth configure-docker --quiet
docker pull "gcr.io/${PROJECT}/ubuntu1404:java8" &
docker pull "gcr.io/${PROJECT}/ubuntu1604:java8" &
docker pull "gcr.io/${PROJECT}/ubuntu1804:java11" &
docker pull "gcr.io/${PROJECT}/ubuntu1804:nojava" &
wait

# Allow the Buildkite agent to access Docker images on GCR.
sudo -H -u buildkite-agent gcloud auth configure-docker --quiet

# Write the Buildkite agent configuration.
cat > /etc/buildkite-agent/buildkite-agent.cfg <<EOF
token="${BUILDKITE_TOKEN}"
name="%hostname"
tags="kind=docker,os=linux"
experiment="git-mirrors"
build-path="/var/lib/buildkite-agent/builds"
git-mirrors-path="/var/lib/bazelbuild"
hooks-path="/etc/buildkite-agent/hooks"
plugins-path="/etc/buildkite-agent/plugins"
EOF

# Add the Buildkite agent hooks.
cat > /etc/buildkite-agent/hooks/environment <<EOF
#!/bin/bash

set -euo pipefail

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin:/snap/google-cloud-sdk/current/bin"
export ANDROID_HOME=/opt/android-sdk-linux
export ANDROID_NDK_HOME=/opt/android-ndk-r15c
export BUILDKITE_ARTIFACT_UPLOAD_DESTINATION="gs://${ARTIFACT_BUCKET}/\$BUILDKITE_JOB_ID"
EOF

# Fix permissions of the Buildkite agent configuration files and hooks.
chmod 0400 /etc/buildkite-agent/buildkite-agent.cfg
chmod 0500 /etc/buildkite-agent/hooks/*
chown -R buildkite-agent:buildkite-agent /etc/buildkite-agent

# Start the Buildkite agent service.
systemctl start buildkite-agent

exit 0
