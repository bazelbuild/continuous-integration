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

# Find all the debian dependencies of a series of debian package,
# using a docker instance as base image. Just run the script to see its
# usage.

cd $(dirname "${BASH_SOURCE[0]}")
echo -n "This will regenerate $PWD/generated.bzl, are you sure? [y/N] "
read ans
if [ "$ans" = "y" -o "$ans" = "Y" ]; then
  ./create_debs_repositories.sh \
    docker:ubuntu:wily \
    ubuntu-wily-amd64 zip,g++,zlib1g-dev,openjdk-8-jdk,openjdk-8-source,wget,git,unzip,python,python3,curl \
    ubuntu-wily-amd64-golang:ubuntu-utopic-amd64 golang,make \
    ubuntu-wily-amd64-ssh:ubuntu-wily-amd64 ssh \
    >generated.bzl
fi
