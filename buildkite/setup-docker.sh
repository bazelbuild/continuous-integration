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
  apt-get -y install python-is-python3 openjdk-11-jdk-headless unzip
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
  if [[ "$(uname -m)" != "aarch64" ]]; then
    ROOT_DEV=$(findmnt -n -o SOURCE /)
    tune2fs -o ^acl,journal_data_writeback,nobarrier "${ROOT_DEV}"
    cat > /etc/fstab <<'EOF'
LABEL=cloudimg-rootfs    /            ext4    defaults,noatime,commit=300,journal_async_commit    0 0
LABEL=UEFI               /boot/efi    vfat    defaults,noatime                                    0 0
EOF
  fi
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
      "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
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

  # Add buildkite-agent to the docker group to grant it permissions to the Docker socket
  usermod -aG docker buildkite-agent
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
  apt-get -y install google-cloud-cli
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
  curl -fsSL -o android-ndk-r15c.zip https://dl.google.com/android/repository/android-ndk-r15c-linux-x86_64.zip
  unzip android-ndk-r15c.zip > /dev/null
  rm android-ndk-r15c.zip
  curl -fsSL -o android-ndk-r25b.zip https://dl.google.com/android/repository/android-ndk-r25b-linux.zip
  unzip android-ndk-r25b.zip > /dev/null
  rm android-ndk-r25b.zip
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
  latest/bin/sdkmanager --update
  latest/bin/sdkmanager \
      "build-tools;36.1.0" \
      "extras;android;m2repository" \
      "platform-tools" \
      "platforms;android-24" \
      "platforms;android-28" \
      "platforms;android-29" \
      "platforms;android-30" \
      "platforms;android-31" \
      "platforms;android-32" > /dev/null
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

### Enable containerd image store.
{
  cat > /etc/docker/daemon.json <<'EOF'
{
  "features": {
    "containerd-snapshotter": true
  }
}
EOF
}

### Configure and start Docker.
systemctl start docker
docker info -f '{{ .DriverStatus }}'

### Ensure that Docker images can be downloaded from GCR.
gcloud auth configure-docker --quiet

### Pull the Docker images that we need in production.

docker pull "gcr.io/bazel-public/rockylinux8@sha256:e35110228b3a4611044e54986d145821bfe226cddf6d436d404a25875f81ab1b" &
docker pull "gcr.io/bazel-public/rockylinux8-java11@sha256:b3737995891f59d44560823b16f12620636ca2934e1d9ea456185f47909d9b70" &
docker pull "gcr.io/bazel-public/rockylinux8-java11-devtoolset10@sha256:437d374f3c41aba2f436f4813893c8cd8b33ff0f7908d65603e5f1e135c3d6f6" &
docker pull "gcr.io/bazel-public/rockylinux8-releaser@sha256:c7cfce3e39fe8ed61e87cf715deeee7a1ca3821189f9cc4476f00f4f8c9534cb" &
docker pull "gcr.io/bazel-public/debian10-java11@sha256:c1e3e07da65ea58dea49efd2d46e7e5d833d344ca42e64c6b9b7065a75ad7710" &
docker pull "gcr.io/bazel-public/debian11-java17@sha256:42da27bb2aa6101b3e03728c0f18e20772e70f708e84d708e4f3a28ea40560d8" &
docker pull "gcr.io/bazel-public/debian12@sha256:1a3cf7132942b72a3855ef81e592a9819dda882cc15856f611b2cbbe5b3b3de7" &
docker pull "gcr.io/bazel-public/debian13@sha256:37aefc308562a763f63ea9c3988a4639754d041c2241ec93da8355ceb83490a4" &
docker pull "gcr.io/bazel-public/ubuntu1804-java11@sha256:25cbb00de12a00485b215440d4ef58469ba305afa54283e40f5b7a8b8ca13c0f" &
docker pull "gcr.io/bazel-public/ubuntu2004-java11@sha256:da0038022a8173e05549fcd003d0af97f7e89a1ee29c6f2e19db10ae7d8dc328" &
docker pull "gcr.io/bazel-public/ubuntu2004@sha256:ffa90e8bad9b3952a40a0f0a9a42e3438faf0002aaa3f20cba6dd2a258ec1a56" &
docker pull "gcr.io/bazel-public/ubuntu2004-kythe@sha256:3862183a7674064e7e36ab851166e5a20eaccb47c8dd7205354fc8de6a6be0e9" &
docker pull "gcr.io/bazel-public/ubuntu2204-kythe@sha256:6c99684b79d9efb14ef812b368d68e4d6f02dd70e667ebbf541b1899421af67e" &
docker pull "gcr.io/bazel-public/ubuntu2404-kythe@sha256:9a1dd748974ec460049ba2ef0d5b8bbb72c33f74abdf9cba7bc8cb2345dfc5a7" &
docker pull "gcr.io/bazel-public/ubuntu2204-java17@sha256:6a9f9efc10e83d97c73ba562745c84740abe07753e04d13c835e482c40df41e6" &
docker pull "gcr.io/bazel-public/ubuntu2204@sha256:07887f6469bb5594b3b86bf6023398356e3791006570695a556086eff13ded74" &
docker pull "gcr.io/bazel-public/ubuntu2404@sha256:4df19f6dfb4fdb99576105689751d3680dd5103770b3739e6a1cda41e9e8a16d" &
docker pull "gcr.io/bazel-public/fedora39-java17@sha256:47a5dd090b4c3d25190bd2bf7ad7ca9985f13ae8c7ff693f1cff87da9270c1cc" &
docker pull "gcr.io/bazel-public/fedora40-java21@sha256:8f6abc2f08a2d55f92ca44b461e7c780f2f653559726b402b4d8d6ec0e4a98ed" &
docker pull "gcr.io/bazel-public/fedora43-java25@sha256:00ce3008b8a95149d3547da5e167372270399419893fba1723fd65daca31b30a" &
wait

poweroff
