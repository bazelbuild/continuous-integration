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

# Stop the agent (which will automatically be restarted) after each job.
disconnect-after-job=true
disconnect-after-job-timeout=86400
EOF
chmod 0400 /etc/buildkite-agent/buildkite-agent.cfg
chown -R buildkite-agent:buildkite-agent /etc/buildkite-agent

# Do not start buildkite-agent automatically. The startup script will start it
# when necessary.
if [[ -e /bin/systemctl ]]; then
  systemctl disable buildkite-agent
  mkdir /etc/systemd/system/buildkite-agent.service.d
  cat > /etc/systemd/system/buildkite-agent.service.d/override.conf <<'EOF'
[Service]
Restart=always
ExecStopPost=/bin/echo "Cleaning up after Buildkite Agent exited ..."
ExecStopPost=/usr/bin/find /tmp -user buildkite-agent -delete
ExecStopPost=/usr/bin/find /var/lib/buildkite-agent -mindepth 1 -maxdepth 1 ! -name builds -execdir rm -rf '{}' +
ExecStopPost=/bin/sh -c 'docker ps -q | xargs -r docker kill'
ExecStopPost=/usr/bin/docker system prune -f --volumes
EOF
else
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
  find /var/lib/buildkite-agent -mindepth 1 -maxdepth 1 ! -name builds -execdir rm -rf '{}' +
  docker ps -q | xargs -r docker kill
  docker system prune -f --volumes
end script
EOF
fi
