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

# Script to easily re-image the various vms on GCE
set -eu

# Shortcut for image name so we can change the image for all slave at once
UBUNTU1404=https://www.googleapis.com/compute/v1/projects/ubuntu-os-cloud/global/images/ubuntu-1404-trusty-v20161020
UBUNTU1604=https://www.googleapis.com/compute/v1/projects/ubuntu-os-cloud/global/images/ubuntu-1604-xenial-v20161020

# List of executor nodes in the following format:
#   GCE-VM-NAME GCE-BASE-IMAGE JENKINS-NODE LOCATION STARTUP-METADATA SETUP-SCRIPTS
# Where
#   GCE-VM-NAME is the VM name on GCE
#   GCE-BASE-IMAGE is the name of the base image in GCE
#                  (see `gcloud compute images list`)
#   JENKINS-NODE is the name of the node in Jenkins
#   LOCATION is the location in GCE (e.g. europe-west1-d)
#   NETWORK is the GCE network the instance has to be created on.
#   STARTUP-METADATA is the metadata argument to gcloud to launch the right
#                    startup script.
#   SETUP-SCRIPTS is a list of shell scripts to adapt the executor node. It should
#                create a ci user with its home in /home/ci
#                and ends with writing to /home/ci/node_name the name
#                of the jenkins node.

# Executor nodes for ci.bazel.io
SLAVES=(
    "ubuntu-14-04-slave-1 $UBUNTU1404 ubuntu_14.04-x86_64-1 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-14-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-14-04-slave-2 $UBUNTU1404 ubuntu_14.04-x86_64-2 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-14-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-14-04-slave-3 $UBUNTU1404 ubuntu_14.04-x86_64-3 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-14-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-14-04-slave-4 $UBUNTU1404 ubuntu_14.04-x86_64-4 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-14-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-14-04-slave-5 $UBUNTU1404 ubuntu_14.04-x86_64-5 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-14-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-14-04-slave-6 $UBUNTU1404 ubuntu_14.04-x86_64-6 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-14-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-14-04-slave-7 $UBUNTU1404 ubuntu_14.04-x86_64-7 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-14-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-14-04-slave-8 $UBUNTU1404 ubuntu_14.04-x86_64-8 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-14-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-16-04-slave-1 $UBUNTU1604 ubuntu_16.04-x86_64-1 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-16-04-slave-2 $UBUNTU1604 ubuntu_16.04-x86_64-2 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-16-04-slave-3 $UBUNTU1604 ubuntu_16.04-x86_64-3 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-16-04-slave-4 $UBUNTU1604 ubuntu_16.04-x86_64-4 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-16-04-slave-5 $UBUNTU1604 ubuntu_16.04-x86_64-5 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-16-04-slave-6 $UBUNTU1604 ubuntu_16.04-x86_64-6 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-16-04-slave-7 $UBUNTU1604 ubuntu_16.04-x86_64-7 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-16-04-slave-8 $UBUNTU1604 ubuntu_16.04-x86_64-8 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-docker-slave-1 $UBUNTU1604 ubuntu_16.04-x86_64-docker-1 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh ubuntu-16-04-docker.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-docker-slave-2 $UBUNTU1604 ubuntu_16.04-x86_64-docker-2 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh ubuntu-16-04-docker.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-docker-slave-3 $UBUNTU1604 ubuntu_16.04-x86_64-docker-3 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh ubuntu-16-04-docker.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-docker-slave-4 $UBUNTU1604 ubuntu_16.04-x86_64-docker-4 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh ubuntu-16-04-docker.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "freebsd-11-slave-1 https://www.googleapis.com/compute/v1/projects/freebsd-org-cloud-dev/global/images/freebsd-11-0-stable-amd64-2017-01-06 freebsd-11-1 europe-west1-d default startup-script=jenkins-slave.sh freebsd-slave.sh freebsd-ci-homedir.sh"
    "freebsd-11-slave-2 https://www.googleapis.com/compute/v1/projects/freebsd-org-cloud-dev/global/images/freebsd-11-0-stable-amd64-2017-01-06 freebsd-11-2 europe-west1-d default startup-script=jenkins-slave.sh freebsd-slave.sh freebsd-ci-homedir.sh"
    "freebsd-11-slave-3 https://www.googleapis.com/compute/v1/projects/freebsd-org-cloud-dev/global/images/freebsd-11-0-stable-amd64-2017-01-06 freebsd-11-3 europe-west1-d default startup-script=jenkins-slave.sh freebsd-slave.sh freebsd-ci-homedir.sh"
    "freebsd-11-slave-4 https://www.googleapis.com/compute/v1/projects/freebsd-org-cloud-dev/global/images/freebsd-11-0-stable-amd64-2017-01-06 freebsd-11-4 europe-west1-d default startup-script=jenkins-slave.sh freebsd-slave.sh freebsd-ci-homedir.sh"
    "freebsd-12-slave-1 https://www.googleapis.com/compute/v1/projects/freebsd-org-cloud-dev/global/images/freebsd-12-0-current-amd64-2017-07-04 freebsd-12-1 europe-west1-d default startup-script=jenkins-slave.sh freebsd-slave.sh freebsd-ci-homedir.sh"
    "freebsd-12-slave-2 https://www.googleapis.com/compute/v1/projects/freebsd-org-cloud-dev/global/images/freebsd-12-0-current-amd64-2017-07-04 freebsd-12-2 europe-west1-d default startup-script=jenkins-slave.sh freebsd-slave.sh freebsd-ci-homedir.sh"
    "freebsd-12-slave-3 https://www.googleapis.com/compute/v1/projects/freebsd-org-cloud-dev/global/images/freebsd-12-0-current-amd64-2017-07-04 freebsd-12-3 europe-west1-d default startup-script=jenkins-slave.sh freebsd-slave.sh freebsd-ci-homedir.sh"
    "freebsd-12-slave-4 https://www.googleapis.com/compute/v1/projects/freebsd-org-cloud-dev/global/images/freebsd-12-0-current-amd64-2017-07-04 freebsd-12-4 europe-west1-d default startup-script=jenkins-slave.sh freebsd-slave.sh freebsd-ci-homedir.sh"
    # Fow Windows, we use a custom image with pre-installed MSVC.
    "windows-slave-1 windows-server-2012-r2-dc-v20160112-vs2015-cpp-python-msys windows-x86_64-1 europe-west1-d default windows-startup-script-ps1=jenkins-slave-windows.ps1"
    "windows-slave-2 windows-server-2012-r2-dc-v20160112-vs2015-cpp-python-msys windows-x86_64-2 europe-west1-d default windows-startup-script-ps1=jenkins-slave-windows.ps1"
    "windows-slave-3 windows-server-2012-r2-dc-v20160112-vs2015-cpp-python-msys windows-x86_64-3 europe-west1-d default windows-startup-script-ps1=jenkins-slave-windows.ps1"
    "windows-slave-4 windows-server-2012-r2-dc-v20160112-vs2015-cpp-python-msys windows-x86_64-4 europe-west1-d default windows-startup-script-ps1=jenkins-slave-windows.ps1"
    # For benchmark
    "ubuntu-16-04-benchmark-slave $UBUNTU1604 ubuntu_16.04-x86_64-benchmark-1 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
)

# Jenkins controller for ci.bazel.io
MASTER=(
    # VM name
    "jenkins"
    # Zone
    "europe-west1-d"
    # Metadata specification
    "google-container-manifest=jenkins.yml,startup-script=mount-volumes.sh"
    # Disk specification
    "name=jenkins-volumes,device-name=volumes"
    # Address name
    "ci"
    # Network name
    "default"
)

# Executor nodes for ci-staging.bazel.io
STAGING_SLAVES=(
    "ubuntu-14-04-slave-staging $UBUNTU1404 ubuntu_14.04-x86_64-staging europe-west1-d staging startup-script=jenkins-slave.sh ubuntu-14-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-16-04-slave-staging $UBUNTU1604 ubuntu_16.04-x86_64-staging europe-west1-d staging startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-docker-slave-staging $UBUNTU1604 ubuntu_16.04-x86_64-docker-staging europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh ubuntu-16-04-docker.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "freebsd-11-slave-staging https://www.googleapis.com/compute/v1/projects/freebsd-org-cloud-dev/global/images/freebsd-11-0-stable-amd64-2017-01-06 freebsd-11-staging europe-west1-d staging startup-script=jenkins-slave.sh freebsd-slave.sh freebsd-ci-homedir.sh"
    "freebsd-12-slave-staging https://www.googleapis.com/compute/v1/projects/freebsd-org-cloud-dev/global/images/freebsd-12-0-current-amd64-2017-07-04 freebsd-12-staging europe-west1-d staging startup-script=jenkins-slave.sh freebsd-slave.sh freebsd-ci-homedir.sh"
    # Fow Windows, we use a custom image with pre-installed MSVC.
    "windows-slave-staging windows-server-2012-r2-dc-v20160112-vs2015-cpp-python-msys windows-x86_64-staging europe-west1-d staging windows-startup-script-ps1=jenkins-slave-windows.ps1"
    # Remote Cache
    "remote-cache-staging $UBUNTU1604 remote-cache-staging europe-west1-d staging startup-script=start-remote-cache.sh setup-remote-cache.sh"
)
STAGING_MASTER=(
    # VM name
    "jenkins-staging"
    # Zone
    "europe-west2-a"
    # Metadata specification
    "google-container-manifest=jenkins-staging.yml,startup-script=mount-volumes.sh"
    # Disk specification
    "name=jenkins-volumes-staging,device-name=volumes"
    # Address name
    "ci-staging"
    # Network name
    "staging"
)

cd "$(dirname "${BASH_SOURCE[0]}")"

source utils/commands.sh

# Create the container engine VM containing the jenkins instance.
function create_master() {
  local flavour="${1:-}"
  local name="$1"
  local location="$2"
  local metadata="$3"
  local disk="$4"
  local address="$5"
  local network="$6"
  gcloud compute instances create "$name" --tags jenkins \
         --zone "$location" --machine-type n1-standard-4 \
         --image-family container-vm --image-project google-containers \
         --metadata-from-file "$metadata" \
         --boot-disk-type pd-ssd --boot-disk-size 40GB \
         --network "$network" \
         --address "$address" --disk "$disk"
}

# Create a node named $1 whose image is $2 (see `gcloud compute image list`)
# and whose jenkins node name is $3. The other arguments are a list of setup
# scripts to run as root on instance creation. The `jenkins-slave.sh` script
# will be used as the startup script for the instance.
function create_slave() {
  local TAG="$1"
  local IMAGE="$2"
  local JENKINS_NODE="$3"
  local LOCATION="$4"
  local NETWORK="$5"
  local STARTUP_METADATA="$6"
  shift 6

  if [[ $IMAGE == ubuntu-* ]]; then
    IMAGE_FLAG="--image-project=ubuntu-os-cloud --image-family=$IMAGE"
  else
    IMAGE_FLAG="--image $IMAGE"
  fi

  gcloud compute instances create "$TAG" \
      --zone "$LOCATION" --machine-type n1-standard-16 \
      --network "$NETWORK" \
      $IMAGE_FLAG \
      --metadata jenkins_node="$JENKINS_NODE" \
      --boot-disk-type pd-ssd --boot-disk-size 500GB
  case "$TAG" in
    windows-*)  # Windows
      ;;

    freebsd*) # FreeBSD
      # Wait a bit for the VM to fully start
      wait_vm "$TAG" "$LOCATION" 120 /usr/bin/true
      # Create the jenkins user, run additional set-up scripts and mark
      # the install process as finished.
      ssh_command "$TAG" "$LOCATION" \
          "pw useradd -n ci -s /usr/local/bin/bash -d /home/ci -m -w no" \
          "echo \"echo -n '$JENKINS_NODE' >/home/ci/node_name\" | su -m ci" \
          "$@"
      ;;

    *)  # Linux
      wait_vm "$TAG" "$LOCATION"  # Wait a bit for the VM to fully start
      # Create the jenkins user, run additional set-up scripts and mark
      # the install process as finished.
      ssh_command "$TAG" "$LOCATION" \
          "sudo adduser --system --home /home/ci ci" \
          "su ci -s /bin/bash -c \"echo -n '$JENKINS_NODE' >/home/ci/node_name\"" \
          "$@"
      ;;
  esac

  gcloud compute instances stop "$TAG" \
      --zone "$LOCATION"

  gcloud compute instances add-metadata "$TAG" \
      --zone "$LOCATION" \
      --metadata-from-file "$STARTUP_METADATA"

  gcloud compute instances start "$TAG" \
      --zone "$LOCATION"
}

# Updates the --metadata and --metadata-from-file values of an existing VM.
#
# Primary purpose is to propagate changes to the startup scripts (e.g.
# mount-volumes.sh for the jenkins controller, jenkins-slave.sh for Ubuntu nodes,
# etc.) without recreating the VM. The update needs a VM reboot to take effect.
#
# The gcloud command takes a few moments to complete so it is started as a
# background job. Wait on its PID or job number (or %?gcloud) before exiting
# this script.
function update_metadata() {
  local tag="${MASTER[0]}"
  local metadata_flag=""
  local location="${MASTER[1]}"
  local startup_metadata="${MASTER[2]}"

  if [ "$1" = "jenkins-staging" ]; then
    tag="${STAGING_MASTER[0]}"
    metadata_flag=""
    location="${STAGING_MASTER[1]}"
    startup_metadata="${STAGING_MASTER[2]}"
  elif [ ! "$1" = jenkins ]; then
    local args="$(get_slave_by_name "$1")"
    [ -n "$args" ] || (echo "Unknown vm $1" >&2; exit 1)

    tag="$(echo $args | cut -d' ' -f1)"
    metadata_flag="--metadata jenkins_node=$(echo $args | cut -d' ' -f3)"
    location="$(echo $args | cut -d' ' -f4)"
    startup_metadata="$(echo $args | cut -d' ' -f6)"
  fi

  gcloud compute instances add-metadata "$tag" \
      --zone "$location" \
      $metadata_flag \
      --metadata-from-file "$startup_metadata" &
}

function get_slave_by_name() {
  for i in "${SLAVES[@]}" "${STAGING_SLAVES[@]}"; do
    if [[ "$i" =~ ^"$1 " ]]; then
      echo "$i"
    fi
  done
}

function create_vm() {
  if [ "$1" = "jenkins" ]; then
    create_master "${MASTER[@]}"
  elif [ "$1" = "jenkins-staging" ]; then
    create_master "${STAGING_MASTER[@]}"
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
    $action jenkins-staging
    for i in "${SLAVES[@]}" "${STAGING_SLAVES[@]}"; do
      $action "${i%% *}"
    done
  elif (( $# == 1 )) && [ "$1" = "prod" ]; then
    $action jenkins
    for i in "${SLAVES[@]}"; do
      $action "${i%% *}"
    done
  elif (( $# == 1 )) && [ "$1" = "staging" ]; then
    $action jenkins-staging
    for i in "${STAGING_SLAVES[@]}"; do
      $action "${i%% *}"
    done
  else
    for i in "$@"; do
      $action "$i"
    done
  fi
  wait %?gcloud 2>/dev/null || true  # wait fails if the job already finished.
}

function test_slave() {
  local TAG=$1
  if test_vm $TAG; then
    if [ "$TAG" = "${MASTER[0]}" ]; then
      echo "${MASTER[1]}"
    elif [ "$TAG" =  "${STAGING_MASTER[0]}" ]; then
      echo "${STAGING_MASTER[1]}"
    else
      get_slave_by_name "$TAG" | cut -d " " -f 4
    fi
  fi
}

function vm_command() {
  local command=$1
  local TAG=$2
  local location="$(test_slave "$TAG")"
  shift 2
  if [ -n "$location" ]; then
    gcloud compute instances $command --quiet --zone=$location $TAG "$@"
  fi
}

function delete_vm() {
  vm_command delete "$@"
}

function stop_vm() {
  vm_command stop "$@"
}

function start_vm() {
  vm_command start "$@"
}

function do_ssh_command() {
  tag=$1
  shift
  location="$(test_slave "${tag}")"
  if [ -z "${location}" ]; then
    echo "Slave ${tag} was not found or is not running" >&2
  else
    ssh_command "$tag" "$location" "$@"
  fi
}

command="${1-}"
shift || true

case "${command}" in
  "stop")
    action stop_vm "$@"
    ;;
  "start")
    action start_vm "$@"
    ;;
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
  "update_metadata")
    action update_metadata "$@"
    ;;
  "ssh_command")
    do_ssh_command "$@"
    ;;
  "ssh")
    tag=$1
    location="$(test_slave "${tag}")"
    if [ -z "${location}" ]; then
      echo "Slave ${tag} was not found or is not running" >&2
    else
      gcloud compute ssh "$tag" --zone "$location"
    fi
    ;;
  "kill_container")
    tag="$1"
    do_ssh_command "$1" 'sudo docker stop $(sudo docker ps -q -f status=running -f ancestor='"$2"')'
    ;;
  *)
    echo "Usage: $0 <command> ([<vm> ... <vm>]|staging|prod)" >&2
    echo "       $0 ssh_command <vm> <arg0> [<arg1>..<argN>]" >&2
    echo "       $0 ssh <vm>" >&2
    echo "       $0 kill_container <vm> <image>" >&2
    echo " - command can be:" >&2
    echo "    create: create the VM, fails if the VM already exists." >&2
    echo "    delete: delete the VM, fails if the VM does not exists." >&2
    echo "    reimage: reimage the VM, equivalent to delete followed by create." >&2
    echo "    update_metadata: update the VM metadata, the VM must already exists." >&2
    echo "    start: start the VM, the VM must exists." >&2
    echo "    stop: stop the VM, the VM must exists." >&2
    echo " - ssh_command executes a command via SSH on the specified VM." >&2
    echo " - ssh launch a secure shell on the specified VM." >&2
    echo " - kill_container kills container that runs the specified image on the" >&2
    echo "   specified VM." >&2
    echo "Special value 'staging' and 'prod' point to all VM in, respectively," >&2
    echo "ci-staging.bazel.io and ci.bazel.io." >&2
    exit 1
    ;;
esac
