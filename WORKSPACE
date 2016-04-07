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

# Jenkins plugins
load("//jenkins:plugins.bzl", "jenkins_plugins")
jenkins_plugins()

# Docker base images
load("//base:docker_pull.bzl", "docker_pull")
docker_pull(
    name = "ubuntu-wily",
    tag = "ubuntu:wily",
)

docker_pull(
    name = "jenkins",
    tag = "jenkins:1.642.4",
)

# Docker debian deps
load("//base:debs.bzl", "docker_debs_repositories")
docker_debs_repositories()

# Releases stuff
http_file(
    name = "hoedown",
    sha256 = "779b75397043f6f6cf2ca8c8a716da58bb03ac42b1a21b83ff66b69bc60c016c",
    url = "https://github.com/hoedown/hoedown/archive/3.0.4.tar.gz",
)

http_file(
    name = "github_release",
    sha256 = "d6994f8a43aaa7c5a7c8c867fe69cfe302cd8eda0df3d371d0e69413999c83d8",
    url = "https://github.com/c4milo/github-release/archive/v1.0.7.tar.gz",
)
