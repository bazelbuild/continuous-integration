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

# Mount the permanent volumes for the Docker image.

set -eu

mkdir -p /volumes
mount -t ext4 /dev/disk/by-id/google-volumes /volumes

mkdir -p /volumes/{jenkins_home,secrets}
# Allow ci (1000) user from docker images to access those directory.
# We use the uid because the host do not have the ci user.
chown 1000 /volumes/{jenkins_home,secrets}
