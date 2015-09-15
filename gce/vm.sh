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

# Script to easily re-image the various vms on GCE
set -eu

# List of slaves in the following format:
#   GCE-VM-NAME GCE-BASE-IMAGE JENKINS-NODE SETUP-SCRIPTS
# Where
#   GCE-VM-NAME is the VM name on GCE
#   GCE-BASE-IMAGE is the name of the base image in GCE
#                  (see `gcloud compute images list`)
#   JENKINS-NODE
#   SETUP-SCRIPTS is a list of shell scripts to adapt the slave. It should
#                create a ci user with its home in /home/ci
#                and ends with writing to /home/ci/node_name the name
#                of the jenkins node.
SLAVES=(
    "ubuntu-14-04-slave ubuntu-14-04 ubuntu_14.04-x86_64 ubuntu-14-04-slave.sh linux-android.sh"
    "ubuntu-14-10-slave ubuntu-14-10 ubuntu_14.10-x86_64 ubuntu-14-10-slave.sh linux-android.sh"
)

cd "$(dirname "${BASH_SOURCE[0]}")"

# Test whether $1 is the name of an existing instance on GCE
function test_vm() {
  (( $(gcloud compute instances list "$1" | wc -l) > 1 ))
}

# Create the container engine VM containing the jenkins instance.
function create_master() {
  gcloud compute instances create jenkins --tags jenkins \
         --zone us-central1-a --machine-type n1-standard-4 \
         --image container-vm \
         --metadata-from-file google-container-manifest=jenkins.yml,startup-script=mount-volumes.sh \
         --boot-disk-type pd-ssd --boot-disk-size 40GB \
         --address ci --disk name=jenkins-volumes,device-name=volumes
}

# Create a slave named $1 whose image is $2 (see `gcloud compute image list`)
# and whose jenkins node name is $3. The other arguments are a list of setup
# scripts to run as root on instance creation. The `jenkins-slave.sh` script
# will be used as the startup script for the instance.
function create_slave() {
  local TAG="$1"
  local IMAGE="$2"
  local JENKINS_NODE="$3"
  shift 3
  gcloud compute instances create $TAG \
         --zone us-central1-a --machine-type n1-standard-8 \
         --image $IMAGE \
         --metadata-from-file startup-script=jenkins-slave.sh \
         --boot-disk-type pd-ssd --boot-disk-size 80GB
  sleep 1  # Wait a bit for the VM to fully start
  # Create the Jenkins user
  gcloud compute ssh --zone=us-central1-a \
         --command "sudo adduser --system --home /home/ci ci" $TAG
  # Runs additional set-up scripts
  for i in "$@"; do
    cat $i | gcloud compute ssh --zone=us-central1-a \
                    --command "cat >/tmp/setup.sh" $TAG
    gcloud compute ssh --zone=us-central1-a \
           --command "sudo bash /tmp/setup.sh" $TAG
  done
  # Finally mark the install process as finished
  echo "$JENKINS_NODE" | \
      gcloud compute ssh --zone=us-central1-a \
             --command "sudo su ci -s /bin/bash -c 'cat >/home/ci/node_name'" \
             $TAG
}

function get_slave_by_name() {
  for i in "${SLAVES[@]}"; do
    if [[ "$i" =~ ^"$1 " ]]; then
      echo "$i"
    fi
  done
}

function create_vm() {
  if [ "$1" = "jenkins" ]; then
    create_master
  else
    local args="$(get_slave_by_name "$1")"
    [ -n "$args" ] || (echo "Unknown vm $1" >&2; exit 1)
    create_slave $args
  fi
}

function action() {
  local action=$1
  shift
  if (( $# == 0 )); then
    $action jenkins
    for i in "${SLAVES[@]}"; do
      $action "${i%% *}"
    done
  else
    for i in "$@"; do
      $action "$i"
    done
  fi
}

function delete_vm() {
  local TAG=$1
  if test_vm $TAG; then
    gcloud compute instances delete --zone=us-central1-a $TAG
  fi
}

command="${1-}"
shift || true

case "${command}" in
  "create")
    action create_vm "$@"
    ;;
  "delete")
    action delete_vm "$@"
    ;;
  "reimage")
    action delete_vm "$@"
    action create_vm "$@"
    ;;
  *)
    echo "Usage: $0 (create|delete|reimage) [vm ... vm]" >&2
    exit 1
    ;;
esac
