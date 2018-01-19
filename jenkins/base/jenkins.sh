#!/bin/bash
#
# Copyright 2015 The Bazel Authors. All rights reserved.
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

# Script to run Jenkins from the Docker image
set -eux

# Take file $1 and copy it to file $2, replacing all instance of
# the string '##SECRET:filename##' by the content of the file
# 'filename' for each file in /opt/secrets
function replace_secrets() {
  if [ "${1##*.}" = "xml" ]; then
    # Only do replacement for xml files
    local content="$(cat $1)"
    for i in /opt/secrets/*; do
      local bi="$(basename $i)"
      if echo -n "${content}" | grep -qF "##SECRET:${bi}##"; then
        content="$(echo -n "${content}" | sed "s|##SECRET:${bi}##|$(cat $i)|g")"
      fi
    done
    # Environment
    for i in $(compgen -v); do
      if echo -n "${content}" | grep -qF "##ENV:${i}##"; then
        local var="$(printenv "$i")"
        content="$(echo -n "${content}" | sed "s|##ENV:${i}##|${var}|g")"
      fi
    done
    echo -n "${content}" >$2
  else
    cp $1 $2
  fi
}
export -f replace_secrets

# Remove existing jobs configuration so we delete jobs
# We do not use find because it goes too deep, use a function instead
delete_jobs() {
  for i in "$1/jobs/"*; do
    if [ -d "$i" ]; then
      if [ -f "$i/config.xml" ]; then
        rm -f "$i/config.xml"
      fi
      delete_jobs "$i"
    fi
  done
}
delete_jobs /var/jenkins_home

# Same for nodes
rm -rf /var/jenkins_home/nodes
# Remove existing plugins to ensure update of plugins
rm -fr /var/jenkins_home/plugins

# Copy the configuration files provided in the docker image
(cd /usr/share/jenkins/ref && \
    find ./ -type f -exec bash -c \
    "mkdir -p /var/jenkins_home/\$(dirname '{}'); \
     rm -f '/var/jenkins_home/{}'; \
     replace_secrets '/usr/share/jenkins/ref/{}' '/var/jenkins_home/{}'" \;)

# Transform /opt/lib to a git repository if exists to be used
# as a pipeline library (GitSCM).
if [ -d "/opt/lib" ]; then
  (cd /opt/lib && \
      git init && \
      git config user.email "nobody@nowhere.local" && \
      git config user.name "Nobody" && \
      git add . && \
      git commit -m "Jenkins library: commit from container")
fi

# Execute Jenkins
JAVA_OPTS="${JAVA_OPTS-} -Dorg.jenkinsci.plugins.ghprb.GhprbTrigger.disableRegisterOnStartup=true"
exec java ${JAVA_OPTS-} -jar /usr/share/jenkins/jenkins.war ${JENKINS_OPTS-} "$@"
