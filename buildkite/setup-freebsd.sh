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
## Building Bazel from source also needs bash, which is not in the base
## system and which every bootstrap script names in its shebang; a JDK;
## and python3, since rules_python ships no CPython for FreeBSD and the
## build falls back to the system interpreter.
pkg install -y \
  bash \
  bazel \
  git \
  openjdk21 \
  python3 \
  wget \
  zip

## Mount procfs and fddescfs.
mount -t fdescfs fdesc /dev/fd
mount -t procfs proc /proc
cat >> /etc/fstab <<EOF
fdesc   /dev/fd         fdescfs         rw      0       0
proc    /proc           procfs          rw      0       0
EOF
