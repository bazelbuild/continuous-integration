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
export PATH="$PATH:/snap/bin:/snap/google-cloud-sdk/current/bin"

# Optimize the CPU scheduler for throughput.
# (see https://unix.stackexchange.com/questions/466722/how-to-change-the-length-of-time-slices-used-by-the-linux-cpu-scheduler/466723)
sysctl -w kernel.sched_min_granularity_ns=10000000
sysctl -w kernel.sched_wakeup_granularity_ns=15000000
sysctl -w vm.dirty_ratio=40
#echo always > /sys/kernel/mm/transparent_hugepage/enabled

# Use the local SSDs as fast storage.
for device in /dev/nvme0n?; do
  mkswap $device
  swapon --discard -p0 $device
done
swapon -s

# Create filesystem for buildkite-agent's home.
AGENT_HOME="/var/lib/buildkite-agent"
mount -t tmpfs -o size=250G tmpfs "${AGENT_HOME}"
mkdir -p "${AGENT_HOME}/.cache/bazel/_bazel_buildkite-agent"
chown -R buildkite-agent:buildkite-agent "${AGENT_HOME}"
chmod 0755 "${AGENT_HOME}"

# Create filesystem for Docker.
DOCKER_HOME="/var/lib/docker"
mount -t tmpfs -o size=250G tmpfs "${DOCKER_HOME}"
chown -R root:root "${DOCKER_HOME}"
chmod 0711 "${DOCKER_HOME}"

# Let 'localhost' resolve to '::1', otherwise one of Envoy's tests fails.
sed -i 's/^::1 .*/::1 localhost ip6-localhost ip6-loopback/' /etc/hosts

# Get configuration parameters.
case $(hostname -f) in
  *.bazel-public.*)
    ARTIFACT_BUCKET="bazel-trusted-buildkite-artifacts"
    BUILDKITE_TOKEN=$(gsutil cat "gs://bazel-trusted-encrypted-secrets/buildkite-trusted-agent-token.enc" | \
        gcloud kms decrypt --project bazel-public --location global --keyring buildkite --key buildkite-trusted-agent-token --ciphertext-file - --plaintext-file -)
    ;;
  *.bazel-untrusted.*)
    case $(hostname -f) in
      *-testing-*)
        ARTIFACT_BUCKET="bazel-testing-buildkite-artifacts"
        BUILDKITE_TOKEN=$(gsutil cat "gs://bazel-testing-encrypted-secrets/buildkite-testing-agent-token.enc" | \
            gcloud kms decrypt --project bazel-untrusted --location global --keyring buildkite --key buildkite-testing-agent-token --ciphertext-file - --plaintext-file -)
        ;;
      *)
        ARTIFACT_BUCKET="bazel-untrusted-buildkite-artifacts"
        BUILDKITE_TOKEN=$(gsutil cat "gs://bazel-untrusted-encrypted-secrets/buildkite-untrusted-agent-token.enc" | \
            gcloud kms decrypt --project bazel-untrusted --location global --keyring buildkite --key buildkite-untrusted-agent-token --ciphertext-file - --plaintext-file -)
        ;;
    esac
esac

# Configure and start Docker.
systemctl start docker

# Pull some known images so that we don't have to download / extract them on each CI job.
gcloud auth configure-docker --quiet
docker pull "gcr.io/bazel-public/ubuntu1604:java8" &
docker pull "gcr.io/bazel-public/ubuntu1804:java11" &
docker pull "gcr.io/bazel-public/ubuntu1804:nojava" &
docker pull "gcr.io/bazel-public/centos7:java8" &
wait

# Allow the Buildkite agent to access Docker images on GCR.
sudo -H -u buildkite-agent gcloud auth configure-docker --quiet

# Write the Buildkite agent's systemd configuration.
mkdir -p /etc/systemd/system/buildkite-agent.service.d
cat > /etc/systemd/system/buildkite-agent.service.d/override.conf <<'EOF'
[Service]
# This allows us to run ExecStartPre and ExecStartPost steps with root permissions.
PermissionsStartOnly=true
# Disable tasks accounting, because Bazel is prone to run into resource limits there.
# This fixes the "cgroup: fork rejected by pids controller" error that some CI jobs triggered.
TasksAccounting=no
EOF
systemctl daemon-reload

# Write the Buildkite agent configuration.
cat > /etc/buildkite-agent/buildkite-agent.cfg <<EOF
token="${BUILDKITE_TOKEN}"
name="%hostname"
tags="queue=default,kind=docker,os=linux"
experiment="git-mirrors"
build-path="/var/lib/buildkite-agent/builds"
git-mirrors-path="/var/lib/gitmirrors"
hooks-path="/etc/buildkite-agent/hooks"
plugins-path="/etc/buildkite-agent/plugins"
disconnect-after-job=false
disconnect-after-idle-timeout=900
EOF

# Add the Buildkite agent hooks.
cat > /etc/buildkite-agent/hooks/environment <<EOF
#!/bin/bash

set -euo pipefail

export ANDROID_HOME=/opt/android-sdk-linux
export ANDROID_NDK_HOME=/opt/android-ndk-r15c
export BUILDKITE_ARTIFACT_UPLOAD_DESTINATION="gs://${ARTIFACT_BUCKET}/\$BUILDKITE_JOB_ID"
export CLOUDSDK_PYTHON="/usr/bin/python"
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin:/snap/google-cloud-sdk/current/bin"
EOF

cat > /etc/buildkite-agent/hooks/pre-exit <<'EOF'
#!/bin/bash
echo_and_run() { echo "\$ $*" ; "$@" ; }

while [[ $(docker ps -q) ]]; do
  echo_and_run docker kill $(docker ps -q)
done

USED_DISK_PERCENT=$(df --output=pcent /var/lib/docker | tail +2 | cut -d'%' -f1 | tr -d ' ')

if [[ $USED_DISK_PERCENT -ge 80 ]]; then
  echo_and_run docker system prune -a -f --volumes
else
  echo_and_run docker system prune -f --volumes
fi

# Delete all Bazel output bases (but leave the cache and install bases).
echo_and_run find /var/lib/buildkite-agent/.cache/bazel/_bazel_buildkite-agent \
    -mindepth 1 -maxdepth 1 ! -name 'cache' ! -name 'install' -exec chmod -R 0777 {} + \
    -exec rm -rf {} +
EOF

# Fix permissions of the Buildkite agent configuration files and hooks.
chmod 0400 /etc/buildkite-agent/buildkite-agent.cfg
chmod 0500 /etc/buildkite-agent/hooks/*
chown -R buildkite-agent:buildkite-agent /etc/buildkite-agent

# Update our gitmirror.
sudo -H -u buildkite-agent gsutil -qm rsync -rd gs://bazel-git-mirror/mirrors/ /var/lib/gitmirrors/

# Start the Buildkite agent service.
systemctl start buildkite-agent

exit 0
