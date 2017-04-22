#!/bin/bash -eu
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

# A simple utility that copies the content of the groovy library to the test
# jenkins docker container to test modification to the lib.

: "${IMAGE_NAME:=bazel:jenkins-test}"
: "${CONTAINER_NAME:=$(docker ps | grep "${IMAGE_NAME}" | cut -f 1 -d " ")}"

LIB_DIR="$(cd "$(dirname "$0")" && pwd -P)/lib"

if [ -z "$CONTAINER_NAME" ]; then
    echo "Could not find container running bazel:jenkins-test, is the test container running?" >&2
    exit 1
fi

docker exec "$CONTAINER_NAME" bash -c 'rm -fr /opt/lib/*'
for i in "$LIB_DIR/"*; do
    docker cp "$i" "$CONTAINER_NAME:/opt/lib/"
done
docker exec "$CONTAINER_NAME" chown -R jenkins /opt/lib
docker exec "$CONTAINER_NAME" su jenkins bash -c 'cd /opt/lib; git add .; git commit -m sync'
