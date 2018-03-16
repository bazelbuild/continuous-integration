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

###
### Install the Buildkite agent.
###

case $(hostname) in
  *ubuntu*)
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 \
        --recv-keys 32A37959C2FA5C3C99EFBC32A79206696452D198 &> /dev/null
    add-apt-repository -y "deb https://apt.buildkite.com/buildkite-agent unstable main"
    apt-get -qqy update > /dev/null
    apt-get -qqy install buildkite-agent > /dev/null
    ;;
  *)
    echo "Don't know how to install the Buildkite agent on this host: $(hostname)!"
    exit 1
esac

###
### /etc/buildkite-agent/buildkite-agent.cfg
###

# Deduce the operating system from the hostname and put it into the metadata.
case $(hostname) in
  *pipeline*)
    AGENT_TAGS="kind=pipeline,os=pipeline,pipeline=true"
    ;;
  *trusted*)
    AGENT_TAGS="kind=trusted,os=trusted"
    ;;
  *ubuntu1404*)
    AGENT_TAGS="kind=worker,os=ubuntu1404"
    ;;
  *ubuntu1604*)
    AGENT_TAGS="kind=worker,os=ubuntu1604"
    ;;
  *)
    echo "Could not deduce operating system from hostname: $(hostname)!"
    exit 1
esac

AGENT_TAGS="${AGENT_TAGS},image-version=${IMAGE_VERSION}"

# Write the Buildkite agent configuration.
cat > /etc/buildkite-agent/buildkite-agent.cfg <<EOF
token="xxx"
name="%hostname-%n"
tags="${AGENT_TAGS}"
tags-from-gcp=true
build-path="/var/lib/buildkite-agent/builds"
hooks-path="/etc/buildkite-agent/hooks"
plugins-path="/etc/buildkite-agent/plugins"
EOF

# Stop the agent after each job on stateless worker machines.
if [[ $(hostname) != *pipeline* ]]; then
  cat >> /etc/buildkite-agent/buildkite-agent.cfg <<EOF
disconnect-after-job=true
disconnect-after-job-timeout=86400
EOF
fi

###
### /etc/buildkite-agent/hooks/environment
###

# Add the Buildkite agent hooks.
cat > /etc/buildkite-agent/hooks/environment <<EOF
#!/bin/bash

set -euo pipefail

export ANDROID_HOME="/opt/android-sdk-linux"
echo "Android SDK is at \${ANDROID_HOME}"

export ANDROID_NDK_HOME="/opt/android-ndk-*"
echo "Android NDK is at \${ANDROID_NDK_HOME}"

export BUILDKITE_ARTIFACT_UPLOAD_DESTINATION="gs://bazel-buildkite-artifacts/\$BUILDKITE_JOB_ID"
export BUILDKITE_GS_ACL="publicRead"

export BUILDKITE_IMAGE_VERSION="${IMAGE_VERSION}"
echo "Running image is version \${BUILDKITE_IMAGE_VERSION}"
EOF

# The trusted worker machine may only execute certain whitelisted builds.
if [[ $(hostname) == *trusted* ]]; then
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

###
### Service configuration.
###

# Some notes about our service config:
#
# - All Buildkite agents except the pipeline agent are stateless and need a special service config
#   that kills remaining processes and deletes temporary files.
#
# - We set the service to not launch automatically, as the startup script will start it once it is
#   done with setting up the local SSD and writing the agent configuration.
if [[ $(hostname) == *pipeline* ]]; then
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
ExecStopPost=/usr/bin/find /var/lib/buildkite-agent -mindepth 1 -maxdepth 1 ! -name builds -execdir rm -rf '{}' +
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
  find /var/lib/buildkite-agent -mindepth 1 -maxdepth 1 ! -name builds -execdir rm -rf '{}' +
  docker ps -q | xargs -r docker kill
  docker system prune -f --volumes
end script
EOF
else
  echo "Unknown operating system - has neither systemd nor upstart?"
  exit 1
fi
