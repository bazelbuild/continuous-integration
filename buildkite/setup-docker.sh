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
  apt-get -y update
  apt-get -y dist-upgrade
  apt-get -y install python openjdk-8-jdk unzip
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

### Install the Buildkite Agent on production images.
{
  apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 \
      --recv-keys 32A37959C2FA5C3C99EFBC32A79206696452D198
  add-apt-repository -y "deb https://apt.buildkite.com/buildkite-agent stable main"
  apt-get -y update
  apt-get -y install buildkite-agent

  # Disable the Buildkite agent service, as the startup script has to mount /var/lib/buildkite-agent
  # first.
  systemctl disable buildkite-agent
}

### Install Docker.
{
  apt-get -y install apt-transport-https ca-certificates

  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
  add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

  apt-get -y update
  apt-get -y install docker-ce

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

# Preseed our Git mirrors.
{
  mkdir -p /var/lib/gitmirrors
  curl -fsSL https://storage.googleapis.com/bazel-git-mirror/bazelbuild-mirror.tar | \
      tar x -C /var/lib/gitmirrors --strip=1
  # gsutil -qm rsync -rd gs://bazel-git-mirror/mirrors/ /var/lib/gitmirrors/
  chown -R buildkite-agent:buildkite-agent /var/lib/gitmirrors
  chmod -R 0755 /var/lib/gitmirrors
}

# Install Swift toolchains.
{
  curl -fsSL https://swift.org/builds/swift-4.2.1-release/ubuntu1404/swift-4.2.1-RELEASE/swift-4.2.1-RELEASE-ubuntu14.04.tar.gz | \
      tar xz -C /opt
  curl -fsSL https://swift.org/builds/swift-4.2.1-release/ubuntu1604/swift-4.2.1-RELEASE/swift-4.2.1-RELEASE-ubuntu16.04.tar.gz | \
      tar xz -C /opt
  curl -fsSL https://swift.org/builds/swift-4.2.1-release/ubuntu1804/swift-4.2.1-RELEASE/swift-4.2.1-RELEASE-ubuntu18.04.tar.gz | \
      tar xz -C /opt
}

# Install Go.
{
  mkdir /opt/go1.12.6.linux-amd64
  curl -fsSL https://dl.google.com/go/go1.12.6.linux-amd64.tar.gz | \
      tar xz -C /opt/go1.12.6.linux-amd64 --strip=1
}

# Install Android NDK.
{
  cd /opt
  curl -fsSL -o android-ndk.zip https://dl.google.com/android/repository/android-ndk-r15c-linux-x86_64.zip
  unzip android-ndk.zip > /dev/null
  rm android-ndk.zip
}

# Install Android SDK.
{
  mkdir -p /opt/android-sdk-linux
  cd /opt/android-sdk-linux
  curl -fsSL -o android-sdk.zip https://dl.google.com/android/repository/sdk-tools-linux-4333796.zip
  unzip android-sdk.zip > /dev/null
  rm android-sdk.zip
  yes | tools/bin/sdkmanager --licenses > /dev/null || true
  tools/bin/sdkmanager --update
  tools/bin/sdkmanager \
      "build-tools;27.0.3" \
      "build-tools;28.0.2" \
      "emulator" \
      "extras;android;m2repository" \
      "platform-tools" \
      "platforms;android-24" \
      "platforms;android-28" \
      "system-images;android-19;default;x86" \
      "system-images;android-21;default;x86" \
      "system-images;android-22;default;x86" \
      "system-images;android-23;default;x86"
}

# Fix permissions in /opt.
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
