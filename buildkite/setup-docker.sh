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
  apt-get -qqy dist-upgrade
  apt-get -qqy install zfsutils-linux
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
      --recv-keys 32A37959C2FA5C3C99EFBC32A79206696452D198
  add-apt-repository -y "deb https://apt.buildkite.com/buildkite-agent stable main"
  apt-get -qqy update
  apt-get -qqy install buildkite-agent

  # Disable the Buildkite agent service, as the startup script has to mount /var/lib/buildkite-agent
  # first.
  systemctl disable buildkite-agent

  mkdir /etc/systemd/system/buildkite-agent.service.d
  cat > /etc/systemd/system/buildkite-agent.service.d/override.conf <<'EOF'
[Service]
Restart=always
PermissionsStartOnly=true
# Disable tasks accounting, because Bazel is prone to run into resource limits there.
# This fixes the "cgroup: fork rejected by pids controller" error that some CI jobs triggered.
TasksAccounting=no
EOF

  mkdir /etc/systemd/system/buildkite-agent@.service.d
  cat > /etc/systemd/system/buildkite-agent@.service.d/override.conf <<'EOF'
[Service]
Restart=always
PermissionsStartOnly=true
Environment=BUILDKITE_AGENT_NAME=%%hostname-%i
Environment=BUILDKITE_AGENT_PRIORITY=%i
# Disable tasks accounting, because Bazel is prone to run into resource limits there.
# This fixes the "cgroup: fork rejected by pids controller" error that some CI jobs triggered.
TasksAccounting=no
EOF
}

### Install Docker.
{
  apt-get -qqy install apt-transport-https ca-certificates

  curl -sSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
  add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

  apt-get -qqy update
  apt-get -qqy install docker-ce

  # Allow the buildkite-agent user access to Docker.
  usermod -aG docker buildkite-agent

  # Disable the Docker service and related stuff, as the startup script has to mount
  # /var/lib/docker first.
  systemctl disable containerd
  systemctl disable docker
}

### Setup Bazelisk.
# TODO: We can remove this, once we run the "Setup" step inside a Docker container, too.
# TODO: Automatically fetch the latest release.
{
  curl -Lo /usr/local/bin/bazel https://github.com/philwo/bazelisk/releases/download/v0.0.3/bazelisk-linux-amd64
  chown root:root /usr/local/bin/bazel
  chmod 0755 /usr/local/bin/bazel
}

### Setup KVM.
{
  apt-get -qqy install qemu-kvm
  usermod -a -G kvm buildkite-agent

  echo 'KERNEL=="kvm", NAME="%k", GROUP="kvm", MODE="0666"' > /etc/udev/rules.d/65-kvm.rules
}

### Clean up and trim the filesystem (potentially reduces the final image size).
{
  rm -rf /var/lib/apt/lists/*
  fstrim -v /
  sleep 3
}

poweroff
