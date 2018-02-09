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

# $BAZEL_VERSION is set in install-bazel.sh.
mkdir -p /root/bazel
cd /root/bazel
curl -sSLo /root/bazel-dist.zip "https://releases.bazel.build/${BAZEL_VERSION}/release/bazel-${BAZEL_VERSION}-dist.zip"
unzip /root/bazel-dist.zip > /dev/null
rm /root/bazel-dist.zip

source /etc/buildkite-agent/hooks/environment
bazel build --spawn_strategy=linux-sandbox -- //src:bazel //src/test/... -//src/test/docker/...
bazel clean --expunge

cd /root
rm -rf /root/bazel
