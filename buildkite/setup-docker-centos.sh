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
    yum -y clean expire-cache
    yum -y update
    yum -y upgrade
    yum -y install nfs-utils
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
  cat >> /etc/security/limits.d/20-nofile.conf <<'EOF'
*                soft    nofile          100000
*                hard    nofile          100000
EOF
}

### We need to remap a few system users and groups to other UIDs and GIDs, so that we can use
### the numbers for buildkite-agent and Docker.
{
  getent group input | grep ':999:' || {
    echo "Group input did not have the expected GID 999, exiting"
    exit 1
  }
  getent passwd chrony | grep ':998:996:' || {
    echo "User chrony did not have the expected UID 998 and GID 996, exiting"
    exit 1
  }
  getent passwd polkitd | grep ':999:998:' || {
    echo "User polkitd did not have the expected UID 999 and GID 998, exiting"
    exit 1
  }
  sed -i 's/input:x:999:/input:x:900:/' /etc/group
  sed -i 's/chrony:x:996:/chrony:x:901:/' /etc/group
  sed -i 's/polkitd:x:998:/polkitd:x:902:/' /etc/group
  sed -i 's/chrony:x:998:996:/chrony:x:901:901:/' /etc/passwd
  sed -i 's/polkitd:x:999:998:/polkitd:x:902:902:/' /etc/passwd
  find / -xdev -gid 999 -exec chgrp -v input '{}' +
  find / -xdev -uid 998 -exec chown -v chrony '{}' +
  find / -xdev -gid 996 -exec chgrp -v chrony '{}' +
  find / -xdev -uid 999 -exec chown -v polkitd '{}' +
  find / -xdev -gid 998 -exec chgrp -v polkitd '{}' +
  killall chronyd
  killall polkitd
}

### Install the Buildkite Agent on production images.
{
  groupadd -g 999 buildkite-agent
  useradd -d /var/lib/buildkite-agent -g 999 -r -s /bin/bash -u 999 buildkite-agent

  cat > /etc/yum.repos.d/buildkite-agent.repo <<'EOF'
[buildkite-agent]
name = Buildkite Pty Ltd
baseurl = https://yum.buildkite.com/buildkite-agent/stable/x86_64/
enabled=1
gpgcheck=0
priority=1
EOF
  yum -y install buildkite-agent

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
}

### Install Docker.
{
  yum -y install yum-utils
  yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
  yum -y install docker-ce docker-ce-cli containerd.io
  groupmod -g 998 docker

  # Allow the buildkite-agent user access to Docker.
  usermod -aG docker buildkite-agent
}

### Setup KVM.
{
  yum -y install qemu-kvm
  echo 'KERNEL=="kvm", NAME="%k", GROUP="kvm", MODE="0666"' > /etc/udev/rules.d/65-kvm.rules
}

# Preseed our Git mirrors.
{
  mkdir -p /var/lib/bazelbuild
  curl https://storage.googleapis.com/bazel-git-mirror/bazelbuild-mirror.tar | tar x -C /var/lib
  chown -R buildkite-agent:buildkite-agent /var/lib/bazelbuild
  chmod -R 0755 /var/lib/bazelbuild
}

### Install ZFS on Linux.
{
  yum -y install http://download.zfsonlinux.org/epel/zfs-release.el7_6.noarch.rpm
  yum -y install kernel-devel zfs
}



### Clean up and trim the filesystem (potentially reduces the final image size).
{
  yum -y clean expire-cache
  fstrim -v /
  sleep 3
}

poweroff
