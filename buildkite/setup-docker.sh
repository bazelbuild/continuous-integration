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

### Setup script for an Ubuntu 18.04 LTS based Docker host.

# Fail on errors.
# Fail when using undefined variables.
# Print all executed commands.
# Fail when any command in a pipe fails.
set -euxo pipefail

### Prevent dpkg / apt-get / debconf from trying to access stdin.
export DEBIAN_FRONTEND="noninteractive"

### Install base packages.
{
  apt-get -y update
  apt-get -y dist-upgrade
  apt-get -y install python-is-python3 openjdk-11-jdk unzip
}

### Disable automatic upgrades, as they can interfere with our startup scripts.
{
  cat > /etc/apt/apt.conf.d/10periodic <<'EOF'
APT::Periodic::Enable "0";
EOF
}

### Increase file descriptor limits
{
  cat >> /etc/security/limits.conf <<'EOF'
*                soft    nofile          100000
*                hard    nofile          100000
EOF
}

### Patch the filesystem options to increase I/O performance
{
  tune2fs -o ^acl,journal_data_writeback,nobarrier /dev/sda1
  cat > /etc/fstab <<'EOF'
LABEL=cloudimg-rootfs    /            ext4    defaults,noatime,commit=300,journal_async_commit    0 0
LABEL=UEFI               /boot/efi    vfat    defaults,noatime                                    0 0
EOF
}

### Install the Buildkite Agent on production images.
{
  apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 \
      --recv-keys 32A37959C2FA5C3C99EFBC32A79206696452D198
  add-apt-repository -y "deb https://apt.buildkite.com/buildkite-agent stable main"
  apt-get -y update
  apt-get -y install buildkite-agent
  # Workaround bug https://github.com/bazelbuild/continuous-integration/issues/1034
  # curl -fsSL --retry 3 https://github.com/buildkite/agent/releases/download/v3.22.1/buildkite-agent-linux-amd64-3.22.1.tar.gz | \
  #     tar xvz -C /usr/bin ./buildkite-agent

  # Disable the Buildkite agent service, as the startup script has to mount /var/lib/buildkite-agent
  # first.
  systemctl disable buildkite-agent

  mkdir -p /etc/systemd/system/buildkite-agent.service.d
  cat > /etc/systemd/system/buildkite-agent.service.d/10-oneshot-agent.conf <<'EOF'
[Service]
# Only run one job, then shutdown the machine (so that the instance group replaces it with a fresh one).
Restart=no
PermissionsStartOnly=true
ExecStopPost=/bin/systemctl poweroff
EOF

  cat > /etc/systemd/system/buildkite-agent.service.d/10-disable-tasks-accounting.conf <<'EOF'
[Service]
# Disable tasks accounting, because Bazel is prone to run into resource limits there.
# This fixes the "cgroup: fork rejected by pids controller" error that some CI jobs triggered.
TasksAccounting=no
EOF

  cat > /etc/systemd/system/buildkite-agent.service.d/10-environment.conf <<'EOF'
[Service]
# Setup some environment variables that we need.
Environment=ANDROID_HOME=/opt/android-sdk-linux
Environment=ANDROID_NDK_HOME=/opt/android-ndk-r15c
Environment=CLOUDSDK_PYTHON=/usr/bin/python
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
EOF
}

### Let 'localhost' resolve to '::1', otherwise one of Envoy's tests fails.
{
  sed -i 's/^::1 .*/::1 localhost ip6-localhost ip6-loopback/' /etc/hosts
}

### Install Docker.
{
  apt-get -y install apt-transport-https ca-certificates

  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
  echo \
      "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

  apt-get -y update
  apt-get -y install docker-ce docker-ce-cli containerd.io

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
  apt-get -y install qemu-kvm

  # Allow everyone access to the KVM device. As above, this would usually not be a good idea, but
  # these machines are untrusted anyway...
  echo 'KERNEL=="kvm", GROUP="kvm", MODE="0666"' > /etc/udev/rules.d/65-kvm.rules
}

## Add our minimum uptime enforcer.
{
  cat > /etc/systemd/system/minimum-uptime.service <<'EOF'
[Unit]
Description=Ensures that the VM is running for at least one minute.

[Service]
Type=simple
ExecStart=/usr/bin/nohup sleep 60
TimeoutSec=60
KillSignal=SIGHUP

[Install]
WantedBy=multi-user.target
EOF
  systemctl enable minimum-uptime.service
}

### Get rid of Ubuntu's snapd stuff and install the Google Cloud SDK the traditional way.
{
  apt-get -y remove --purge snapd
  echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | \
      tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
  apt-get -y install apt-transport-https ca-certificates
  curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
      apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
  apt-get -y update
  apt-get -y install google-cloud-sdk
}

### Preseed our Git mirrors.
{
  mkdir -p /var/lib/gitmirrors
  curl -fsSL https://storage.googleapis.com/bazel-git-mirror/bazelbuild-mirror.tar | \
      tar x -C /var/lib/gitmirrors --strip=1
  chown -R buildkite-agent:buildkite-agent /var/lib/gitmirrors
  chmod -R 0755 /var/lib/gitmirrors
}

### Install Android NDK.
{
  cd /opt
  curl -fsSL -o android-ndk.zip https://dl.google.com/android/repository/android-ndk-r15c-linux-x86_64.zip
  unzip android-ndk.zip > /dev/null
  rm android-ndk.zip
}

### Install Android SDK.
{
  mkdir -p /opt/android-sdk-linux/cmdline-tools
  cd /opt/android-sdk-linux/cmdline-tools
  curl -fsSL -o android-sdk.zip https://dl.google.com/android/repository/commandlinetools-linux-7302050_latest.zip
  unzip android-sdk.zip > /dev/null
  rm android-sdk.zip
  mv cmdline-tools latest
  yes | latest/bin/sdkmanager --licenses > /dev/null || true
  latest/tools/bin/sdkmanager --update
  latest/tools/bin/sdkmanager \
      "build-tools;28.0.2" \
      "build-tools;29.0.2" \
      "build-tools;29.0.3" \
      "build-tools;30.0.1" \
      "emulator" \
      "extras;android;m2repository" \
      "platform-tools" \
      "platforms;android-24" \
      "platforms;android-28" \
      "platforms;android-29" \
      "platforms;android-30" \
      "system-images;android-19;default;x86" \
      "system-images;android-21;default;x86" \
      "system-images;android-22;default;x86" \
      "system-images;android-23;default;x86"
}

### Fix permissions in /opt.
{
  chown -R root:root /opt
}

### Clean up and trim the filesystem (potentially reduces the final image size).
{
  rm -rf /var/lib/apt/lists/*
  fstrim -v /
  sleep 3
}

poweroff
