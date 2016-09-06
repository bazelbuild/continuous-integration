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

# Creates an empty E2FS disk on GCE
set -eu

function create_disk() {
  local name="$1"
  local zone="${2:-$(gcloud config list compute/zone | grep zone | sed -E 's/ *zone *= *([^ ]*) */\1/')}"
  size="${3:-1024GB}"

  log "Creating disk ${name}"
  gcloud compute disks create "${name}" --size="${size}" --zone="${zone}"

  log "Creating a VM temp-create-disk-${name} for formatting disk ${name}"
  gcloud compute instances create "temp-create-disk-${name}" --zone="${zone}" \
     --image ubuntu-14-04 --boot-disk-type pd-ssd \
     --machine-type n1-standard-1 --disk "name=${name},device-name=volumes"
  # Wait for the VM to be up and running
  wait_vm "temp-create-disk-${name}" "${zone}"
  log "Formatting disk ${name} on temp-create-disk-${name}"
  ssh_command "temp-create-disk-${name}" "${zone}" \
    "yes | mkfs.ext4 -t ext4 /dev/disk/by-id/google-volumes"
  log "Deleting VM temp-creat-disk-${name}"
  echo y | gcloud compute instances delete --zone "${zone}" "temp-create-disk-${name}"
}

