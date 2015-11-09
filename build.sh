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

# Pull dependencies from docker hub, build the docker images and push them
# to GCR.

# Images to pull from docker hub in form "image_name=tar_file"
PULL_IMAGES=(
    "jenkins:1.609.2=jenkins/jenkins-base.tar"
    "ubuntu:wily=base/ubuntu-wily-base.tar"
)
# Image to push to GCR in the form "bazel-target=image_name"
PUSH_IMAGES=(
    "//jenkins:jenkins=jenkins-master"
    "//jenkins:deploy.docker=deploy-slave"
)

BAZEL_GCR_PROJECT="bazel-public"

cd "$(dirname ${BASH_SOURCE[0]})"
set -eu

DRY_RUN=

# A little wrapper to allow dry runs
function run() {
  if [ "$DRY_RUN" ]; then
    echo "$@"
  else
    "$@"
  fi
}

function config() {
  if [ ! -f "jenkins/config.bzl" ]; then
    echo "The admin list file does not exists!" >&2
    echo -n "Enter a comma separated list of admin emails:"
    read emails
    if [ -z "$emails" ]; then
      echo "ADMIN_USERS = []" > jenkins/config.bzl
    else
      echo "ADMIN_USERS = [\"$(echo "${emails}" | sed 's/ *, */", "/g')\"]" \
           >jenkins/config.bzl
    fi
  fi
}

# Pull an image from docker hub and save it to a tar file if the tar file does
# not exist
function pull() {
  local docker_image="$(echo "$i" | cut -d "=" -f 1)"
  local tar_image="$(echo "$i" | cut -d "=" -f 2)"
  if [ ! -f "${tar_image}" ]; then
    echo "Pulling ${docker_image}..."
    run docker pull "${docker_image}"
    run docker save "${docker_image}" >"${tar_image}"
  else
    echo "${tar_image} already here, skipping pulling ${docker_image}"
  fi
}

# Build an image and load it in the local docker registry
function build() {
  local bazel_target="$(echo "$i" | cut -d "=" -f 1)"
  local docker_tag="$(echo "$i" | cut -d "=" -f 2)"
  run bazel run "${bazel_target}" "gcr.io/${BAZEL_GCR_PROJECT}/${docker_tag}"
}

# Push to GCR
function push() {
  local docker_tag="$(echo "$i" | cut -d "=" -f 2)"
  run gcloud docker push "gcr.io/${BAZEL_GCR_PROJECT}/${docker_tag}"
}

function pull_all() {
  for i in "${PULL_IMAGES[@]}"; do
    pull "$i"
  done
}

function build_all() {
  for i in "${PUSH_IMAGES[@]}"; do
    build "$i"
  done
}

function push_all() {
  for i in "${PUSH_IMAGES[@]}"; do
    push "$i"
  done
}

function do_push() {
  pull_all
  build_all
  push_all
}

command="${1-}"
if [[ "$command" =~ dry-(.*) ]]; then
  DRY_RUN=1
  command=${BASH_REMATCH[1]}
else
  config
fi

case "$command" in
  "push")
      do_push
      ;;
  "pull")
      pull_all
      ;;
  "build")
      pull_all
      build_all
      ;;
  *)
      echo "Usage: $0 [dry-](push|pull|build)" >&2
      exit 1
      ;;
esac

