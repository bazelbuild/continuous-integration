#!/bin/bash
#
# Copyright 2016 The Bazel Authors. All rights reserved.
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

# This is a generated files that loads all docker layer built by "docker_push".

RUNFILES="${PYTHON_RUNFILES:-${BASH_SOURCE[0]}.runfiles}"

DOCKER="${DOCKER:-docker}"
GCLOUD="${GCLOUD:-gcloud}"

# List all images identifier (only the identifier) from the local
# docker registry.
IMAGES="$("${DOCKER}" images -aq)"
IMAGE_LEN=$(for i in $IMAGES; do echo -n $i | wc -c; done | sort -g | head -1 | xargs)

[ -n "$IMAGE_LEN" ] || IMAGE_LEN=64

function incr_load() {
  # Load a layer if and only if the layer is not in "$IMAGES", that is
  # in the local docker registry.
  name=$(cat ${RUNFILES}/$1)
  if (echo "$IMAGES" | grep -q ^${name:0:$IMAGE_LEN}$); then
    echo "Skipping $name, already loaded."
  else
    echo "Loading $name..."
    "${DOCKER}" load -i ${RUNFILES}/$2
  fi
}

function tag_last_load() {
  # Tag the last layer.
  if [ -n "${name}" ]; then
    TAG="%{repository}:$1"
    echo "Tagging ${name} as ${TAG}"
    "${DOCKER}" tag -f ${name} ${TAG}
  fi
}

# List of 'incr_load' statements for all layers and
# 'tag_last_load' for each docker image. This generated and
# injected by docker_push.
%{load_statements}

for tag in %{tags}; do
  "${GCLOUD}" docker push "%{repository}:${tag}"
done
