#!/bin/bash
#
# Copyright 2017 The Bazel Authors. All rights reserved.
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

# Deduce the operating system from the hostname and put it into the metadata.
case $(hostname) in
  *ubuntu1404*)
    osname="ubuntu1404"
    ;;
  *ubuntu1604*)
    osname="ubuntu1604"
    ;;
  default)
    echo "Could not deduce operating system from hostname: $(hostname)!"
    exit 1
esac

if [[ $(hostname) == *ubuntu* ]]; then
  apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 32A37959C2FA5C3C99EFBC32A79206696452D198 &> /dev/null
  add-apt-repository -y "deb https://apt.buildkite.com/buildkite-agent unstable main"
  apt-get -qqy update > /dev/null
  apt-get -qqy install buildkite-agent > /dev/null
fi

cat > /etc/buildkite-agent/hooks/environment <<'EOF'
#!/bin/bash

set -eu

export ANDROID_HOME="/opt/android-sdk-linux"
export ANDROID_NDK_HOME="/opt/android-ndk-r14b"
export BUILDKITE_ARTIFACT_UPLOAD_DESTINATION="gs://bazel-buildkite-artifacts/$BUILDKITE_JOB_ID"
export BUILDKITE_GS_ACL="publicRead"
EOF
chmod 0500 /etc/buildkite-agent/hooks/*
chown -R buildkite-agent:buildkite-agent /etc/buildkite-agent

cat > /etc/buildkite-agent/buildkite-agent.cfg <<EOF
token="xxx"
name="%hostname"
tags="os=${osname},pipeline=true"
tags-from-gcp=true
build-path="/var/lib/buildkite-agent/builds"
hooks-path="/etc/buildkite-agent/hooks"
plugins-path="/etc/buildkite-agent/plugins"
timestamp-lines=true

# Stop the agent (which will trigger a reboot of the VM) after each job.
disconnect-after-job=true
disconnect-after-job-timeout=86400
EOF
chmod 0400 /etc/buildkite-agent/buildkite-agent.cfg
chown -R buildkite-agent:buildkite-agent /etc/buildkite-agent

# Do not start buildkite-agent automatically. The startup script will start it
# when necessary.
if [[ -e /bin/systemctl ]]; then
  systemctl disable buildkite-agent

  # Configure the buildkite-agent service so that it reboots the VM when the
  # agent exits.
  mkdir /etc/systemd/system/buildkite-agent.service.d
  cat > /etc/systemd/system/buildkite-agent.service.d/override.conf <<'EOF'
[Service]
# The difference between ExecStop and ExecStopPost is that the former only runs
# when the service started up successfully. This is probably more useful for us,
# as we want to be able to ssh into the VM and debug why the buildkite-agent
# fails to start, instead of going into a reboot loop.
ExecStop=/sbin/reboot

# This is required as otherwise /sbin/reboot is executed as the buildkite-agent
# user and won't have permissions to actually reboot the system.
PermissionsStartOnly=true

# We don't want to restart the service when it stops, as we're going to reboot
# the entire VM.
Restart=no
EOF
else
  cat > /etc/init/buildkite-agent.conf <<'EOF'
description "buildkite-agent"

manual

exec start-stop-daemon --start \
    --quiet \
    --chuid buildkite-agent \
    --pidfile "/var/run/buildkite-agent.pid" \
    --make-pidfile \
    --exec /usr/bin/buildkite-agent -- start

post-stop exec /sbin/reboot
EOF
fi
