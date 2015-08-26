#!/bin/bash
#
# Copyright 2015 Google Inc. All rights reserved.
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

# Copy the configuration files provided in the docker image
(cd /usr/share/jenkins/ref && \
    find ./ -type f -exec bash -c \
    "mkdir -p /var/jenkins_home/\$(dirname '{}'); \
     rm -f '/var/jenkins_home/{}'; \
     cp '/usr/share/jenkins/ref/{}' '/var/jenkins_home/{}'" \;)

# Execute Jenkins
exec java ${JAVA_OPTS-} -jar /usr/share/jenkins/jenkins.war ${JENKINS_OPTS-} "$@"
