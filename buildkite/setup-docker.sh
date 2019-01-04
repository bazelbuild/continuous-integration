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

# Setup script for an Ubuntu 18.04 LTS based Docker host.

# Fail on errors.
# Fail when using undefined variables.
# Print all executed commands.
# Fail when any command in a pipe fails.
set -euxo pipefail

# Prevent dpkg / apt-get / debconf from trying to access stdin.
export DEBIAN_FRONTEND="noninteractive"

### Install base packages.
{
  apt-get -qqy update
  apt-get -qqy dist-upgrade > /dev/null
}

### Increase file descriptor limits
{
cat >> /etc/security/limits.conf <<EOF
*                soft    nofile          100000
*                hard    nofile          100000
EOF
}

### Install the Buildkite Agent on production images.
{
  apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 \
      --recv-keys 32A37959C2FA5C3C99EFBC32A79206696452D198 &> /dev/null
  add-apt-repository -y "deb https://apt.buildkite.com/buildkite-agent stable main"
  apt-get -qqy update
  apt-get -qqy install buildkite-agent > /dev/null

  # Write the Buildkite agent configuration.
  cat > /etc/buildkite-agent/buildkite-agent.cfg <<EOF
token="xxx"
name="%hostname-%n"
tags="kind=docker,os=linux"
build-path="/var/lib/buildkite-agent/builds"
hooks-path="/etc/buildkite-agent/hooks"
plugins-path="/etc/buildkite-agent/plugins"
git-clone-flags="-v --reference /var/lib/bazelbuild"
disconnect-after-job=true
disconnect-after-job-timeout=86400
EOF

  # Add the Buildkite agent hooks.
  cat > /etc/buildkite-agent/hooks/environment <<'EOF'
#!/bin/bash

set -euo pipefail

export PATH=$PATH:/usr/lib/google-cloud-sdk/bin:/snap/bin:/snap/google-cloud-sdk/current/bin
export BUILDKITE_ARTIFACT_UPLOAD_DESTINATION="gs://bazel-buildkite-artifacts/$BUILDKITE_JOB_ID"
export BUILDKITE_GS_ACL="publicRead"

gcloud auth configure-docker --quiet
EOF

  # This is a normal worker machine with systemd (e.g. Ubuntu 16.04 LTS).
  systemctl disable buildkite-agent
  mkdir /etc/systemd/system/buildkite-agent.service.d
  cat > /etc/systemd/system/buildkite-agent.service.d/override.conf <<'EOF'
[Service]
Restart=always
PermissionsStartOnly=true
# Immediately force a shutdown of the system when the Buildkite agent terminates.
ExecStopPost=/sbin/poweroff --force --force
# Disable tasks accounting, because Bazel is prone to run into resource limits there.
# This fixes the "cgroup: fork rejected by pids controller" error that some CI jobs triggered.
TasksAccounting=no
EOF
}

### Install Docker.
{
  apt-get -qqy install apt-transport-https ca-certificates > /dev/null

  curl -sSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
  add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

  apt-get -qqy update
  apt-get -qqy install docker-ce > /dev/null

  # Allow the buildkite-agent user access to Docker.
  usermod -aG docker buildkite-agent

  # Use our caching Docker registry.
  cat > /etc/docker/daemon.json <<'EOF'
{
  "insecure-registries" : ["docker-cache.europe-west1-c.c.bazel-public.internal:5000"]
}
EOF

  # Disable the Docker service, as the startup script has to mount
  # /var/lib/docker first.
  systemctl disable docker
}

### Download a static bundle of all our Git repositories and unpack it.
{
  rm -rf /var/lib/bazelbuild
  curl -sS https://storage.googleapis.com/bazel-git-mirror/bazelbuild.tar | tar x -C /var/lib
  chown -R root:root /var/lib/bazelbuild
  chmod -R 0755 /var/lib/bazelbuild
}

### Clean up and trim the filesystem (potentially reduces the final image size).
{
  rm -rf /var/lib/apt/lists/*
  fstrim -v /
  sleep 3
}

poweroff
