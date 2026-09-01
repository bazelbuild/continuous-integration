#!/bin/sh
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

# Setup script for FreeBSD.
set -eux

## Install Bazel and its dependencies.
##
## bash and unzip are not in the base system and compile.sh needs both; the
## JDK is needed to build Bazel at all, and python3 by the bootstrap and by
## several of the tools it builds.
pkg install -y \
  bash \
  bazel \
  git \
  gmake \
  openjdk21 \
  python3 \
  unzip \
  wget \
  zip

## Mount procfs and fddescfs.
mount -t fdescfs fdesc /dev/fd
mount -t procfs proc /proc
cat >> /etc/fstab <<EOF
fdesc   /dev/fd         fdescfs         rw      0       0
proc    /proc           procfs          rw      0       0
EOF

## The JDK does not put itself on the path, and the bootstrap reads JAVA_HOME
## rather than searching for one.
cat >> /etc/profile <<EOF
JAVA_HOME=/usr/local/openjdk21
export JAVA_HOME
PATH=\$JAVA_HOME/bin:\$PATH
export PATH
EOF
