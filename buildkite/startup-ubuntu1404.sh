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

set -eu

# Use a local SSD if available, otherwise use a RAM disk for our builds.
if [ -e /dev/nvme0n1 ]; then
  mkfs.ext4 -F /dev/nvme0n1
  mount /dev/nvme0n1 /var/lib/buildkite-agent
  chown -R buildkite-agent:buildkite-agent /var/lib/buildkite-agent
  chmod 0755 /var/lib/buildkite-agent
else
  mount -t tmpfs -o mode=0755,uid=buildkite-agent,gid=buildkite-agent tmpfs /var/lib/buildkite-agent
fi

service buildkite-agent start

exit 0
