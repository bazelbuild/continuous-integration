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

# Setup the various utilities for the deploy image (image that deploy releases).
# This script will be run inside the deploy docker image at the docker instance
# startup.

pushd /opt/data

# gsutil does change, we cannot use http_file as the SHA-256 would change over
# time.
wget https://storage.googleapis.com/pub/gsutil.tar.gz

tar zxf hoedown.tar.gz
tar zxf github-release.tar.gz
tar zxf gsutil.tar.gz

mv hoedown-3.0.4 hoedown
pushd hoedown
make CC=gcc hoedown
popd

mv github-release-1.0.7 github-release
pushd github-release
make
popd

popd

