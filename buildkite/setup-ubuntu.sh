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

# Setup script for Ubuntu 14.04 LTS, 16.04 LTS and 18.04 LTS.

# Fail on errors.
# Fail when using undefined variables.
# Print all executed commands.
# Fail when any command in a pipe fails.
set -euxo pipefail

# Prevent dpkg / apt-get / debconf from trying to access stdin.
export DEBIAN_FRONTEND="noninteractive"

### Deduce image configuration from the hostname.
case $(hostname) in
  *pipeline*)
    config_kind="pipeline"
    ;;
  *trusted*)
    config_kind="trusted"
    ;;
  *testing*)
    config_kind="testing"
    ;;
  *worker*)
    config_kind="worker"
    ;;
  *)
    echo "Could not deduce image kind from hostname: $(hostname)!"
    exit 1
    ;;
esac

case $(hostname) in
  *ubuntu1404*)
    config_os="ubuntu1404"
    ;;
  *ubuntu1604*)
    config_os="ubuntu1604"
    ;;
  *ubuntu1804*)
    config_os="ubuntu1804"
    ;;
  *)
    echo "Could not deduce operating system from hostname: $(hostname)!"
    exit 1
esac

case $(hostname) in
  *nojava*)
    config_java="no"
    ;;
  *java8*)
    config_java="8"
    ;;
  *java9*)
    config_java="9"
    ;;
  *)
    echo "Could not deduce Java version from hostname: $(hostname)!"
    exit 1
esac

### Increase file descriptor limits
{
cat >> /etc/security/limits.conf <<EOF
*                soft    nofile          100000
*                hard    nofile          100000
EOF
}

### Install base packages.
{
  # Android SDK requires 32-bits libraries.
  dpkg --add-architecture i386

  apt-get -qqy update
  apt-get -qqy dist-upgrade > /dev/null

  packages=(
    # Bazel dependencies.
    build-essential
    clang
    curl
    git
    python
    python-dev
    python3
    python3-dev
    unzip
    wget
    xvfb
    zip
    zlib1g-dev

    # Dependencies for Android SDK.
    # https://developer.android.com/studio/troubleshoot.html#linux-libraries
    # https://code.google.com/p/android/issues/detail?id=207212
    expect
    libbz2-1.0:i386
    libncurses5:i386
    libstdc++6:i386
    libz1:i386

    # Dependencies for TensorFlow.
    libcurl3-dev
    swig
    python-enum34
    python-mock
    python-numpy
    python-pip
    python-wheel
    python3-mock
    python3-numpy
    python3-pip
    python3-wheel

    # Required by Envoy: https://github.com/bazelbuild/continuous-integration/issues/218
    automake
    autotools-dev
    cmake
    libtool
    m4

    # Required by our infrastructure.
    lvm2

    # Required by Android projects that launch the Android emulator headlessly
    # (see https://github.com/bazelbuild/continuous-integration/pull/246)
    cpu-checker
    qemu-system-x86
    unzip
    xvfb

    # Required by our release process.
    devscripts
    gnupg
    pandoc
    reprepro
    ssmtp
  )

  # Bazel dependencies.
  if [[ "${config_os}" == "ubuntu1804" ]]; then
    packages+=("coreutils")
  else
    packages+=("realpath")
  fi

  apt-get -qqy install "${packages[@]}" > /dev/null

  # Remove apport, as it's unneeded and uses significant CPU and I/O.
  apt-get -qqy purge apport
}

### Fetch and save image version to file.
{
  IMAGE_VERSION=$(curl -sS "http://metadata.google.internal/computeMetadata/v1/instance/attributes/image-version" -H "Metadata-Flavor: Google")
  echo -n "${IMAGE_VERSION}" > /etc/image-version
}


### Install Azul Zulu (OpenJDK).
if [[ "${config_java}" != "no" ]]; then
  apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 0x219BD9C9
  apt-add-repository 'deb http://repos.azulsystems.com/ubuntu stable main'
  apt-get -qqy update
  apt-get -qqy install zulu-${config_java} > /dev/null
else
  apt-get -qqy purge *openjdk* *zulu*
  apt-get -qqy autoremove --purge
fi

### Install Bazel.
{
  bazel_version=$(curl -sSI https://github.com/bazelbuild/bazel/releases/latest | grep '^Location: ' | sed 's|.*/||' | sed $'s/\r//')
  curl -sSLo install.sh "https://releases.bazel.build/${bazel_version}/release/bazel-${bazel_version}-installer-linux-x86_64.sh"
  bash install.sh > /dev/null
  rm -f install.sh
}

### Install the Buildkite Agent on production images.
if [[ "${config_kind}" != "testing" ]]; then
  apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 \
      --recv-keys 32A37959C2FA5C3C99EFBC32A79206696452D198 &> /dev/null
  add-apt-repository -y "deb https://apt.buildkite.com/buildkite-agent stable main"
  apt-get -qqy update
  apt-get -qqy install buildkite-agent > /dev/null

  # Write the Buildkite agent configuration.
  cat > /etc/buildkite-agent/buildkite-agent.cfg <<EOF
token="xxx"
name="%hostname-%n"
tags="kind=${config_kind},os=${config_os},java=${config_java},image-version=${IMAGE_VERSION}"
build-path="/var/lib/buildkite-agent/builds"
hooks-path="/etc/buildkite-agent/hooks"
plugins-path="/etc/buildkite-agent/plugins"
git-clone-flags="-v --reference /var/lib/bazelbuild"
EOF

  # Stop the agent after each job on stateless worker machines.
  if [[ "${config_kind}" != "pipeline" ]]; then
    cat >> /etc/buildkite-agent/buildkite-agent.cfg <<EOF
disconnect-after-job=true
disconnect-after-job-timeout=86400
EOF
  fi

  # Add the Buildkite agent hooks.
  cat > /etc/buildkite-agent/hooks/environment <<'EOF'
#!/bin/bash

set -euo pipefail

export PATH=$PATH:/snap/bin/
export BUILDKITE_ARTIFACT_UPLOAD_DESTINATION="gs://bazel-buildkite-artifacts/$BUILDKITE_JOB_ID"
export BUILDKITE_GS_ACL="publicRead"
EOF

  # The trusted worker machine may only execute certain whitelisted builds.
  if [[ "${config_kind}" == "trusted" ]]; then
    cat >> /etc/buildkite-agent/hooks/environment <<'EOF'
case ${BUILDKITE_BUILD_CREATOR_EMAIL} in
  *@google.com)
    ;;
  *)
    echo "Build creator not allowed: ${BUILDKITE_BUILD_CREATOR_EMAIL}"
    exit 1
esac
    
case ${BUILDKITE_REPO} in
  https://github.com/bazelbuild/bazel.git|\
  https://github.com/bazelbuild/continuous-integration.git)
    ;;
  *)
    echo "Repository not allowed: ${BUILDKITE_REPO}"
    exit 1
esac

case ${BUILDKITE_ORGANIZATION_SLUG} in
  bazel)
    ;;
  *)
    echo "Organization not allowed: ${BUILDKITE_PIPELINE_SLUG}"
    exit 1
esac

case ${BUILDKITE_PIPELINE_SLUG} in
  google-bazel-presubmit-metrics|\
  release)
    ;;
  *)
    echo "Pipeline not allowed: ${BUILDKITE_PIPELINE_SLUG}"
    exit 1
esac

export BUILDKITE_API_TOKEN=$(gsutil cat "gs://bazel-encrypted-secrets/buildkite-api-token.enc" | \
    gcloud kms decrypt --location "global" --keyring "buildkite" --key "buildkite-api-token" \
        --plaintext-file "-" --ciphertext-file "-")
EOF
  fi

  # Some notes about our service config:
  #
  # - All Buildkite agents except the pipeline agent are stateless and need a special service config
  #   that kills remaining processes and deletes temporary files.
  #
  # - We set the service to not launch automatically, as the startup script will start it once it is
  #   done with setting up the local SSD and writing the agent configuration.
  if [[ "${config_kind}" == "pipeline" ]]; then
    # This is a pipeline worker machine.
    systemctl disable buildkite-agent
  elif [[ $(systemctl --version 2>/dev/null) ]]; then
    # This is a normal worker machine with systemd (e.g. Ubuntu 16.04 LTS).
    systemctl disable buildkite-agent
    mkdir /etc/systemd/system/buildkite-agent.service.d
    cat > /etc/systemd/system/buildkite-agent.service.d/override.conf <<'EOF'
[Service]
Restart=always
PermissionsStartOnly=true
ExecStopPost=/bin/echo "Cleaning up after Buildkite Agent exited ..."
ExecStopPost=/usr/bin/find /tmp -user buildkite-agent -delete
ExecStopPost=/usr/bin/find /var/lib/buildkite-agent -mindepth 1 -maxdepth 1 -execdir rm -rf '{}' +
ExecStopPost=/bin/sh -c 'docker ps -q | xargs -r docker kill'
ExecStopPost=/usr/bin/docker system prune -f --volumes
EOF
  elif [[ $(init --version 2>/dev/null | grep upstart) ]]; then
    # This is a normal worker machine with upstart (e.g. Ubuntu 14.04 LTS).
    cat > /etc/init/buildkite-agent.conf <<'EOF'
description "buildkite-agent"

respawn
respawn limit unlimited

exec sudo -H -u buildkite-agent /usr/bin/buildkite-agent start

# Kill all possibly remaining processes after each build.
post-stop script
  set +e
  set -x

  # Kill all remaining processes.
  killall -q -9 -u buildkite-agent

  # Clean up left-over files.
  find /tmp -user buildkite-agent -delete
  find /var/lib/buildkite-agent -mindepth 1 -maxdepth 1 -execdir rm -rf '{}' +
  docker ps -q | xargs -r docker kill
  docker system prune -f --volumes
end script
EOF
  else
    echo "Unknown operating system - has neither systemd nor upstart?"
    exit 1
  fi
fi

### Install Docker.
{
  apt-get -qqy install apt-transport-https ca-certificates > /dev/null

  # From https://download.docker.com/linux/ubuntu/gpg
  curl -sSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
  add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

  apt-get -qqy update
  apt-get -qqy install docker-ce > /dev/null

  # Allow the buildkite-agent user access to Docker.
  if [[ "${config_kind}" != "testing" ]]; then
    usermod -aG docker buildkite-agent
  fi

  # Disable the Docker service, as the startup script has to mount
  # /var/lib/docker first.
  if [[ -e /bin/systemctl ]]; then
    systemctl disable docker
  else
    echo manual > /etc/init/docker.override
  fi
}

### Install Node.js.
{
  curl -sSL https://deb.nodesource.com/setup_8.x | bash - > /dev/null
  apt-get -qqy install nodejs > /dev/null

  # Required by Gerrit:
  # https://gerrit.googlesource.com/gerrit/+show/master/polygerrit-ui/README.md
  npm install -g \
    typescript \
    fried-twinkie@0.0.15
}

### Install Python 3.6.
{
  if [[ "${config_os}" == "ubuntu1804" ]]; then
    pip3 install requests uritemplate pyyaml github3.py
  else
    packages+=("realpath")
    apt-get -qqy install zlib1g-dev libssl-dev

    PYTHON_VERSION="3.6.5"

    mkdir -p /usr/local/src
    pushd /usr/local/src

    curl -O "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz"
    tar xfJ "Python-${PYTHON_VERSION}.tar.xz"
    rm -f "Python-${PYTHON_VERSION}.tar.xz"
    cd "Python-${PYTHON_VERSION}"

    # Enable the 'ssl' module.
    cat >> Modules/Setup.dist <<'EOF'
_ssl _ssl.c \
       -DUSE_SSL -I/usr/include -I/usr/include/openssl \
       -L/usr/lib -lssl -lcrypto
EOF

    echo "Compiling Python ${PYTHON_VERSION} ..."
    ./configure --quiet --enable-ipv6
    make -s -j8 all > /dev/null
    echo "Installing Python ${PYTHON_VERSION} ..."
    make -s altinstall > /dev/null

    pip3.6 install requests uritemplate pyyaml github3.py

    popd
    rm -rf "/usr/local/src/Python-${PYTHON_VERSION}"
  fi
}

### Enable KVM support.
if [[ "${config_kind}" != "testing" ]]; then
  usermod -a -G kvm buildkite-agent
fi

### Install Android SDK and NDK (only if we have a JVM).
if [[ "${config_java}" != "no" ]]; then
  if [[ "${config_java}" == "9" ]]; then
    export SDKMANAGER_OPTS="--add-modules java.se.ee"
  fi

  # Android NDK
  cd /opt
  curl -sSLo android-ndk.zip https://dl.google.com/android/repository/android-ndk-r15c-linux-x86_64.zip
  unzip android-ndk.zip > /dev/null
  rm android-ndk.zip

  # Android SDK
  mkdir -p /opt/android-sdk-linux
  cd /opt/android-sdk-linux
  curl -sSLo android-sdk.zip https://dl.google.com/android/repository/sdk-tools-linux-3859397.zip
  unzip android-sdk.zip > /dev/null
  rm android-sdk.zip
  expect -c '
set timeout -1
log_user 0
spawn tools/bin/sdkmanager --update
expect {
    "Accept? (y/N)" { exp_send "y\r" ; exp_continue }
    eof
}
'

  # This should be kept in sync with mac/mac-android.sh.
  # build-tools 28.0.1 introduces the new dexer, d8.jar
  tools/bin/sdkmanager \
    "build-tools;27.0.3" \
    "build-tools;28.0.2" \
    "emulator" \
    "extras;android;m2repository" \
    "platform-tools" \
    "platforms;android-24" \
    "platforms;android-25" \
    "platforms;android-26" \
    "platforms;android-27" \
    "platforms;android-28" \
    "system-images;android-19;default;x86" \
    "system-images;android-21;default;x86" \
    "system-images;android-22;default;x86" \
    "system-images;android-23;default;x86" \
    > /dev/null
  chown -R root:root /opt/android*


  if [[ "${config_kind}" != "testing" ]]; then
    cat >> /etc/buildkite-agent/hooks/environment <<'EOF'
export ANDROID_HOME="/opt/android-sdk-linux"
echo "Android SDK is at ${ANDROID_HOME}"

export ANDROID_NDK_HOME="/opt/android-ndk-r15c"
echo "Android NDK is at ${ANDROID_NDK_HOME}"
EOF
  fi
fi

### Install tools required by the release process.
{
  curl -sSL https://github.com/c4milo/github-release/releases/download/v1.1.0/github-release_v1.1.0_linux_amd64.tar.gz | \
    tar xvz -C /usr/local/bin
  chown root:root /usr/local/bin/github-release
  chmod 0755 /usr/local/bin/github-release
}

### Clean up and trim the filesystem (potentially reduces the final image size).
{
  rm -rf /var/lib/apt/lists/*
  fstrim -v /
  sleep 3
}

poweroff
