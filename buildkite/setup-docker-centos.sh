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

### Install base packages.
{
    yum -y upgrade
}

### Increase file descriptor limits
{
  cat >> /etc/security/limits.d/20-nofile.conf <<'EOF'
*                soft    nofile          100000
*                hard    nofile          100000
EOF
}

### Install the Buildkite Agent on production images.
{
  cat > /etc/yum.repos.d/buildkite-agent.repo <<'EOF'
[buildkite-agent]
name = Buildkite Pty Ltd
baseurl = https://yum.buildkite.com/buildkite-agent/stable/x86_64/
enabled=1
gpgcheck=0
priority=1
EOF
  yum -y install buildkite-agent

  # Disable the Buildkite agent service, as the startup script has to mount /var/lib/buildkite-agent
  # first.
  systemctl disable buildkite-agent
}

### Install Docker.
{
  yum -y install yum-utils
  yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
  yum-config-manager --enable docker-ce-test
  yum -y install docker-ce docker-ce-cli containerd.io

  # Allow everyone access to the Docker socket. Usually this would be insane from a security point
  # of view, but these are untrusted throw-away machines anyway, so the risk is acceptable.
  mkdir /etc/systemd/system/docker.socket.d
  cat > /etc/systemd/system/docker.socket.d/override.conf <<'EOF'
[Socket]
SocketMode=0666
EOF

  # Disable the Docker service, as the startup script has to mount /var/lib/docker first.
  systemctl disable docker
  systemctl stop docker
}

### Setup KVM.
{
  yum -y install qemu-kvm

  # Allow everyone access to the KVM device. As above, this would usually not be a good idea, but
  # these machines are untrusted anyway...
  echo 'KERNEL=="kvm", NAME="%k", GROUP="kvm", MODE="0666"' > /etc/udev/rules.d/65-kvm.rules
}

# Preseed our Git mirrors.
{
  mkdir -p /var/lib/gitmirrors
  curl https://storage.googleapis.com/bazel-git-mirror/bazelbuild-mirror.tar | tar x -C /var/lib/gitmirrors --strip=1
  chown -R buildkite-agent:buildkite-agent /var/lib/gitmirrors
  chmod -R 0755 /var/lib/gitmirrors
}

### Clean up and trim the filesystem (potentially reduces the final image size).
{
  yum -y clean expire-cache
  fstrim -v /
  sleep 3
}

poweroff
