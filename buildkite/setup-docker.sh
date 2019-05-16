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
  apt-get -qqy install nfs-common
}

### Add our Cloud Filestore volume to the fstab.
{
  case $(hostname -f) in
    *.bazel-public.*)
      cat >> /etc/fstab <<'EOF'
10.93.166.218:/buildkite /opt nfs defaults 0 2
EOF
      ;;
    *.bazel-untrusted.*)
      cat >> /etc/fstab <<'EOF'
10.76.94.74:/buildkite /opt nfs defaults 0 2
EOF
;;
  esac
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

  cat > /etc/buildkite-agent/hooks/pre-exit <<'EOF'
#!/bin/bash
set -euo pipefail

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
EOF
  chown buildkite-agent:buildkite-agent /etc/buildkite-agent/hooks/*
  chmod 0500 /etc/buildkite-agent/hooks/*

  mkdir -p /var/lib/buildkite-agent
  chown buildkite-agent:buildkite-agent /var/lib/buildkite-agent
  chmod 0755 /var/lib/buildkite-agent
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

### Setup KVM.
{
  apt-get -qqy install qemu-kvm
  usermod -a -G kvm buildkite-agent

  echo 'KERNEL=="kvm", NAME="%k", GROUP="kvm", MODE="0666"' > /etc/udev/rules.d/65-kvm.rules
}

# Preseed our Git mirrors.
{
  mkdir -p /var/lib/bazelbuild
  curl https://storage.googleapis.com/bazel-git-mirror/bazelbuild-mirror.tar | tar x -C /var/lib
  chown -R buildkite-agent:buildkite-agent /var/lib/bazelbuild
  chmod -R 0755 /var/lib/bazelbuild
}

### Clean up and trim the filesystem (potentially reduces the final image size).
{
  rm -rf /var/lib/apt/lists/*
  fstrim -v /
  sleep 3
}

poweroff
