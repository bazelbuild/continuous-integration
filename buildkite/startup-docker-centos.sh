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

# Use the local SSDs as fast Docker storage.
mkfs.ext4 -F /dev/nvme0n1
mount /dev/nvme0n1 /var/lib/docker
chown root:root /var/lib/docker
chmod 0711 /var/lib/docker

mkdir /var/lib/docker/bazel-cache
chown buildkite-agent:buildkite-agent /var/lib/docker/bazel-cache
chmod 0755 /var/lib/docker/bazel-cache

# Get configuration parameters.
case $(hostname -f) in
  *.bazel-public.*)
    PROJECT="bazel-public"
    ARTIFACT_BUCKET="bazel-trusted-buildkite-artifacts"
    # Get the Buildkite Token from GCS and decrypt it using KMS.
    BUILDKITE_TOKEN=$(gsutil cat "gs://bazel-trusted-encrypted-secrets/buildkite-trusted-agent-token.enc" | \
        gcloud kms decrypt --project bazel-public --location global --keyring buildkite --key buildkite-trusted-agent-token --ciphertext-file - --plaintext-file -)
    ;;
  *.bazel-untrusted.*)
    PROJECT="bazel-untrusted"
    ARTIFACT_BUCKET="bazel-untrusted-buildkite-artifacts"
    # Get the Buildkite Token from GCS and decrypt it using KMS.
    BUILDKITE_TOKEN=$(gsutil cat "gs://bazel-untrusted-encrypted-secrets/buildkite-untrusted-agent-token.enc" | \
        gcloud kms decrypt --project bazel-untrusted --location global --keyring buildkite --key buildkite-untrusted-agent-token --ciphertext-file - --plaintext-file -)
    ;;
esac

# Configure and start Docker.
systemctl start docker

# Pull some known images so that we don't have to download / extract them on each CI job.
gcloud auth configure-docker --quiet

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

export ANDROID_HOME=/opt/android-sdk-linux
export ANDROID_NDK_HOME=/opt/android-ndk-r15c
export BUILDKITE_ARTIFACT_UPLOAD_DESTINATION="gs://${ARTIFACT_BUCKET}/\$BUILDKITE_JOB_ID"
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin:/snap/google-cloud-sdk/current/bin"
EOF

# Fix permissions of the Buildkite agent configuration files and hooks.
chmod 0400 /etc/buildkite-agent/buildkite-agent.cfg
chmod 0500 /etc/buildkite-agent/hooks/*
chown -R buildkite-agent:buildkite-agent /etc/buildkite-agent

# Start the Buildkite agent service.
systemctl start buildkite-agent

exit 0
