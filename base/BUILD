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
package(default_visibility = ["//visibility:public"])

load("@bazel_tools//tools/build_defs/docker:docker.bzl", "docker_build")
load(":debs.bzl", "DEB_NAMES")

# Base ubuntu
docker_build(
    name = "ubuntu-wily-amd64",
    base = "ubuntu-wily-base.tar",
    debs = DEB_NAMES["ubuntu-wily-amd64"],
    env = {
        "JAVA_HOME": "/usr/lib/jvm/java-8-openjdk-amd64",
    },
    symlinks = {"/usr/local/bin/java": "/usr/lib/jvm/java-8-openjdk-amd64/bin/java"},
)

# Image support golang and make
docker_build(
    name = "ubuntu-wily-amd64-golang",
    base = ":ubuntu-wily-amd64",
    debs = DEB_NAMES["ubuntu-wily-amd64-golang"],
    symlinks = {"/usr/local/bin/go": "/usr/lib/go/bin/go"},
)

# Support SSH for gerrit deployment
docker_build(
    name = "ubuntu-wily-amd64-ssh",
    base = ":ubuntu-wily-amd64",
    debs = DEB_NAMES["ubuntu-wily-amd64-ssh"],
)
