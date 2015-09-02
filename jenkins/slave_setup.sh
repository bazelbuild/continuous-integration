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

# Scripts to configure a slave in a docker image.

# %{HOME_FS} is replaced by the template engine.
HOME_FS=%{HOME_FS}

# Install certificates
(cd /usr/share/ca-certificates && find -type f -name '*.crt' \
    | sed -e 's|^\./||') > /etc/ca-certificates.conf
update-ca-certificates

# Create the Jenkins user
groupadd -g 1000 ci
useradd -d ${HOME_FS} -r -g 1000 -u 1000 ci
chown ci.ci ${HOME_FS}
cd ${HOME_FS}

# Execute additional setups
for i in /opt/run/*.{,ba}sh; do
  if [ -f "$i" ]; then
    /bin/bash $i
  fi
done

# Run the slaves
wget %{JENKINS_SERVER}/jnlpJars/slave.jar
su ci -c "/usr/local/bin/java -jar slave.jar -jnlpUrl %{JENKINS_SERVER}/computer/%{NODE_NAME}/slave-agent.jnlp -noReconnect"
