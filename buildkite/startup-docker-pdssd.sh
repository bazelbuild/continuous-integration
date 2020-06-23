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

### Prevent dpkg / apt-get / debconf from trying to access stdin.
export DEBIAN_FRONTEND="noninteractive"

### Optimize the CPU scheduler for throughput.
### (see https://unix.stackexchange.com/questions/466722/how-to-change-the-length-of-time-slices-used-by-the-linux-cpu-scheduler/466723)
sysctl -w kernel.sched_min_granularity_ns=10000000
sysctl -w kernel.sched_wakeup_granularity_ns=15000000
sysctl -w vm.dirty_ratio=40

### Mount tmpfs to buildkite-agent's home.
AGENT_HOME="/var/lib/buildkite-agent"
mkdir -p "${AGENT_HOME}/.cache/bazel/_bazel_buildkite-agent"
chown -R buildkite-agent:buildkite-agent "${AGENT_HOME}"
chmod 0755 "${AGENT_HOME}"

### Get configuration parameters.
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

### Configure and start Docker.
systemctl start docker

### Ensure that Docker images can be downloaded from GCR.
gcloud auth configure-docker --quiet
sudo -H -u buildkite-agent gcloud auth configure-docker --quiet

### Write the Buildkite agent configuration.
cat > /etc/buildkite-agent/buildkite-agent.cfg <<EOF
token="${BUILDKITE_TOKEN}"
name="%hostname"
tags="queue=default,kind=docker,os=linux"
experiment="git-mirrors"
build-path="/var/lib/buildkite-agent/builds"
git-mirrors-path="/var/lib/gitmirrors"
git-clone-mirror-flags="-v --bare"
hooks-path="/etc/buildkite-agent/hooks"
plugins-path="/etc/buildkite-agent/plugins"
disconnect-after-job=true
health-check-addr=0.0.0.0:8080
EOF

### Add the Buildkite agent hooks.
cat > /etc/buildkite-agent/hooks/environment <<EOF
#!/bin/bash
set -euo pipefail
export BUILDKITE_ARTIFACT_UPLOAD_DESTINATION="gs://${ARTIFACT_BUCKET}/\${BUILDKITE_JOB_ID}"
EOF

### Fix permissions of the Buildkite agent configuration files and hooks.
chmod 0400 /etc/buildkite-agent/buildkite-agent.cfg
chmod 0500 /etc/buildkite-agent/hooks/*
chown -R buildkite-agent:buildkite-agent /etc/buildkite-agent

### Pull a few popular Docker images in advance.
case $(hostname -f) in
    *-testing-*)
        PREFIX="bazel-public/testing"
        ;;
    *)
        PREFIX="bazel-public"
        ;;
esac

docker pull "gcr.io/$PREFIX/centos7-java8" &
docker pull "gcr.io/$PREFIX/centos7-releaser" &
docker pull "gcr.io/$PREFIX/debian10-java11" &
docker pull "gcr.io/$PREFIX/ubuntu1604-bazel-java8" &
docker pull "gcr.io/$PREFIX/ubuntu1604-java8" &
docker pull "gcr.io/$PREFIX/ubuntu1804-bazel-java11" &
docker pull "gcr.io/$PREFIX/ubuntu1804-bazel-nojava" &
docker pull "gcr.io/$PREFIX/ubuntu1804-java11" &
docker pull "gcr.io/$PREFIX/ubuntu1804-nojava" &
docker pull "gcr.io/$PREFIX/ubuntu2004-java11" &
docker pull "gcr.io/$PREFIX/ubuntu2004-nojava" &
wait

### Start the Buildkite agent service.
systemctl start buildkite-agent

exit 0
