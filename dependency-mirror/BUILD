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

# A slave for mirroring all bazel external dependencies on GCS.
load("@io_bazel_rules_docker//docker:docker.bzl", "docker_build")

docker_build(
    name = "gerrit-github-sync",
    base = "//base:ubuntu-wily-amd64-ssh",
    entrypoint = [
        "/bin/bash",
        "/dependency-mirror.sh",
    ],
    files = [
        "dependency-mirror.sh",
        "check_bazel_deps.py",
    ],
    visibility = ["//visibility:public"],
    volumes = ["/opt/secrets"],
)
