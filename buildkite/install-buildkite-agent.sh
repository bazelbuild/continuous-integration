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

apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 32A37959C2FA5C3C99EFBC32A79206696452D198 &> /dev/null
add-apt-repository -y "deb https://apt.buildkite.com/buildkite-agent stable main"

apt-get -qqy update > /dev/null
apt-get -qqy install buildkite-agent > /dev/null

# Our very secret Buildkite token used to authenticate the agent.
BUILDKITE_TOKEN="xxx"

# Deduce the operating system from the hostname and put it into the metadata.
case $(hostname) in
  *ubuntu1404*)
    osname="ubuntu1404"
    ;;
  *ubuntu1604*)
    osname="ubuntu1604"
    ;;
  *freebsd11*)
    osname="freebsd11"
    ;;
  default)
    echo "Could not deduce operating system from hostname: $(hostname)!"
    exit 1
esac

# Create configuration file for buildkite-agent.
sed -i \
  -e "s/^\(# \)*token=.*/token=\"${BUILDKITE_TOKEN}\"/g" \
  -e "s/^\(# \)*name=.*/name=\"%hostname\"/g" \
  -e "s/^\(# \)*meta-data=.*/meta-data=\"os=$osname\"/g" \
  /etc/buildkite-agent/buildkite-agent.cfg

cat > /etc/buildkite-agent/hooks/environment <<'EOF'
#!/bin/bash

# The `environment` hook will run before all other commands, and can be used
# to set up secrets, data, etc. Anything exported in hooks will be available
# to the build script.
#
# For example:
#
# export SECRET_VAR=token

set -e

export ANDROID_HOME="/opt/android-sdk-linux"
export ANDROID_NDK_HOME="/opt/android-ndk-r14b"
export BUILDKITE_ARTIFACT_UPLOAD_DESTINATION="gs://bazel-buildkite-artifacts/$BUILDKITE_JOB_ID"
EOF

chmod 0400 /etc/buildkite-agent/buildkite-agent.cfg
chmod 0500 /etc/buildkite-agent/hooks/*
chown -R buildkite-agent:buildkite-agent /etc/buildkite-agent

# Do not start buildkite-agent automatically. The startup script will prepare
# the local SSD first and then start it.
if [ "$osname" = "ubuntu1404" ]; then
  echo manual > /etc/init/buildkite-agent.override
fi
