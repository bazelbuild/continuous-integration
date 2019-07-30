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

# Prevent dpkg / apt-get / debconf from trying to access stdin.
export DEBIAN_FRONTEND="noninteractive"

# Optimize the CPU scheduler for throughput.
# (see https://unix.stackexchange.com/questions/466722/how-to-change-the-length-of-time-slices-used-by-the-linux-cpu-scheduler/466723)
sysctl -w kernel.sched_min_granularity_ns=10000000
sysctl -w kernel.sched_wakeup_granularity_ns=15000000
sysctl -w vm.dirty_ratio=40

# Use the local SSDs as fast storage.
for device in /dev/nvme0n?; do
  mkswap $device
  swapon --discard -p0 $device
done
swapon -s

# Create a tmpfs.
mkdir -p /tmpfs
mount -t tmpfs -o size=375G tmpfs /tmpfs
mkdir /tmpfs/{buildkite-agent,docker}

# Mount tmpfs to buildkite-agent's home.
AGENT_HOME="/var/lib/buildkite-agent"
mount --bind /tmpfs/buildkite-agent "${AGENT_HOME}"
mkdir -p "${AGENT_HOME}/.cache/bazel/_bazel_buildkite-agent"
chown -R buildkite-agent:buildkite-agent "${AGENT_HOME}"
chmod 0755 "${AGENT_HOME}"

# Mount a shared NFS repository cache.
REPOCACHE="/var/lib/buildkite-agent/.cache/bazel/_bazel_buildkite-agent/cache/repos"
mkdir -p "${REPOCACHE}"
case $(hostname -f) in
  *.bazel-public.*)
    mount -t nfs 10.112.185.98:/repocache "${REPOCACHE}"
    ;;
  *.bazel-untrusted.*)
    mount -t nfs 10.163.211.226:/repocache "${REPOCACHE}"
    ;;
esac
chown buildkite-agent:buildkite-agent "${REPOCACHE}"
chmod 0755 "${REPOCACHE}"

# Mount tmpfs to Docker's working directory.
DOCKER_HOME="/var/lib/docker"
mount --bind /tmpfs/docker "${DOCKER_HOME}"
chown -R root:root "${DOCKER_HOME}"
chmod 0711 "${DOCKER_HOME}"

# Let 'localhost' resolve to '::1', otherwise one of Envoy's tests fails.
sed -i 's/^::1 .*/::1 localhost ip6-localhost ip6-loopback/' /etc/hosts

# Get configuration parameters.
case $(hostname -f) in
  *.bazel-public.*)
    ARTIFACT_BUCKET="bazel-trusted-buildkite-artifacts"
    BUILDKITE_AGENT_TOKEN=$(gsutil cat "gs://bazel-trusted-encrypted-secrets/buildkite-trusted-agent-token.enc" | \
        gcloud kms decrypt --project bazel-public --location global --keyring buildkite --key buildkite-trusted-agent-token --ciphertext-file - --plaintext-file -)
    BUILDKITE_API_TOKEN=$(gsutil cat "gs://bazel-trusted-encrypted-secrets/buildkite-trusted-api-token.enc" | \
        gcloud kms decrypt --project bazel-public --location global --keyring buildkite --key buildkite-trusted-api-token --ciphertext-file - --plaintext-file -)
    BUILDKITE_ORG="bazel-trusted"
    ;;
  *.bazel-untrusted.*)
    case $(hostname -f) in
      *-testing-*)
        ARTIFACT_BUCKET="bazel-testing-buildkite-artifacts"
        BUILDKITE_AGENT_TOKEN=$(gsutil cat "gs://bazel-testing-encrypted-secrets/buildkite-testing-agent-token.enc" | \
            gcloud kms decrypt --project bazel-untrusted --location global --keyring buildkite --key buildkite-testing-agent-token --ciphertext-file - --plaintext-file -)
        BUILDKITE_API_TOKEN=$(gsutil cat "gs://bazel-testing-encrypted-secrets/buildkite-testing-api-token.enc" | \
            gcloud kms decrypt --project bazel-untrusted --location global --keyring buildkite --key buildkite-testing-api-token --ciphertext-file - --plaintext-file -)
        BUILDKITE_ORG="bazel-testing"
        ;;
      *)
        ARTIFACT_BUCKET="bazel-untrusted-buildkite-artifacts"
        BUILDKITE_AGENT_TOKEN=$(gsutil cat "gs://bazel-untrusted-encrypted-secrets/buildkite-untrusted-agent-token.enc" | \
            gcloud kms decrypt --project bazel-untrusted --location global --keyring buildkite --key buildkite-untrusted-agent-token --ciphertext-file - --plaintext-file -)
        BUILDKITE_API_TOKEN=$(gsutil cat "gs://bazel-untrusted-encrypted-secrets/buildkite-untrusted-api-token.enc" | \
            gcloud kms decrypt --project bazel-untrusted --location global --keyring buildkite --key buildkite-untrusted-api-token --ciphertext-file - --plaintext-file -)
        BUILDKITE_ORG="bazel"
        ;;
    esac
esac

# Configure and start Docker.
systemctl start docker

# Ensure that Docker images can be downloaded from GCR.
gcloud auth configure-docker --quiet
sudo -H -u buildkite-agent gcloud auth configure-docker --quiet

# Write the Buildkite agent's systemd configuration.
mkdir -p /etc/systemd/system/buildkite-agent.service.d
cat > /etc/systemd/system/buildkite-agent.service.d/override.conf <<'EOF'
[Service]
Restart=no
ExecStopPost=/bin/systemctl poweroff
# This allows us to run ExecStartPre and ExecStartPost steps with root permissions.
PermissionsStartOnly=true
# Disable tasks accounting, because Bazel is prone to run into resource limits there.
# This fixes the "cgroup: fork rejected by pids controller" error that some CI jobs triggered.
TasksAccounting=no
EOF
systemctl daemon-reload

# Write the Buildkite agent configuration.
cat > /etc/buildkite-agent/buildkite-agent.cfg <<EOF
token="${BUILDKITE_AGENT_TOKEN}"
name="%hostname"
tags="queue=default,kind=docker,os=linux"
experiment="git-mirrors"
build-path="/var/lib/buildkite-agent/builds"
git-mirrors-path="/var/lib/gitmirrors"
hooks-path="/etc/buildkite-agent/hooks"
plugins-path="/etc/buildkite-agent/plugins"
disconnect-after-job=true
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
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
EOF

# Fix permissions of the Buildkite agent configuration files and hooks.
chmod 0400 /etc/buildkite-agent/buildkite-agent.cfg
chmod 0500 /etc/buildkite-agent/hooks/*
chown -R buildkite-agent:buildkite-agent /etc/buildkite-agent

# Update our gitmirror.
# sudo -H -u buildkite-agent gsutil -qm rsync -rd gs://bazel-git-mirror/mirrors/ /var/lib/gitmirrors/

# Setup the healthcheck service.
curl \
  --retry 10 \
  --fail \
  --output /usr/local/bin/healthcheck \
  --silent \
  --show-error \
  --location \
  https://storage.googleapis.com/bazel-ci/healthcheck/healthcheck-linux-amd64
chmod +x /usr/local/bin/healthcheck

cat > /etc/default/healthcheck <<EOF
BUILDKITE_API_TOKEN=${BUILDKITE_API_TOKEN}
BUILDKITE_ORG=${BUILDKITE_ORG}
EOF
chmod 0600 /etc/default/healthcheck

cat > /etc/systemd/system/healthcheck.service <<'EOF'
[Unit]
Description=Bazel CI Health Check Service
After=network.target

[Service]
Type=simple
EnvironmentFile=/etc/default/healthcheck
ExecStart=/usr/local/bin/healthcheck

[Install]
WantedBy=multi-user.target
EOF

# Start the services.
systemctl daemon-reload
systemctl start buildkite-agent
systemctl start healthcheck

exit 0
