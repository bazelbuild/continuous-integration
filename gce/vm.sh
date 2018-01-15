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

# Executor nodes for ci.bazel.build
SLAVES=(
    "ubuntu-14-04-slave-1 ubuntu-1404-lts ubuntu_14.04-x86_64-1 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-14-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-14-04-slave-2 ubuntu-1404-lts ubuntu_14.04-x86_64-2 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-14-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-14-04-slave-3 ubuntu-1404-lts ubuntu_14.04-x86_64-3 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-14-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-14-04-slave-4 ubuntu-1404-lts ubuntu_14.04-x86_64-4 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-14-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-16-04-slave-1 ubuntu-1604-lts ubuntu_16.04-x86_64-1 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-16-04-slave-2 ubuntu-1604-lts ubuntu_16.04-x86_64-2 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-16-04-slave-3 ubuntu-1604-lts ubuntu_16.04-x86_64-3 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-16-04-slave-4 ubuntu-1604-lts ubuntu_16.04-x86_64-4 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-docker-slave-1 ubuntu-1604-lts ubuntu_16.04-x86_64-docker-1 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh ubuntu-16-04-docker.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-docker-slave-2 ubuntu-1604-lts ubuntu_16.04-x86_64-docker-2 europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh ubuntu-16-04-docker.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "freebsd-11-slave-1 https://www.googleapis.com/compute/v1/projects/freebsd-org-cloud-dev/global/images/freebsd-11-1-stable-amd64-2017-12-28 freebsd-11-1 europe-west1-d default startup-script=jenkins-slave.sh freebsd-slave.sh freebsd-ci-homedir.sh"
    "freebsd-11-slave-2 https://www.googleapis.com/compute/v1/projects/freebsd-org-cloud-dev/global/images/freebsd-11-1-stable-amd64-2017-12-28 freebsd-11-2 europe-west1-d default startup-script=jenkins-slave.sh freebsd-slave.sh freebsd-ci-homedir.sh"
    "freebsd-12-slave-1 https://www.googleapis.com/compute/v1/projects/freebsd-org-cloud-dev/global/images/freebsd-12-0-current-amd64-2017-12-28 freebsd-12-1 europe-west1-d default startup-script=jenkins-slave.sh freebsd-slave.sh freebsd-ci-homedir.sh"
    "freebsd-12-slave-2 https://www.googleapis.com/compute/v1/projects/freebsd-org-cloud-dev/global/images/freebsd-12-0-current-amd64-2017-12-28 freebsd-12-2 europe-west1-d default startup-script=jenkins-slave.sh freebsd-slave.sh freebsd-ci-homedir.sh"
    # Fow Windows, we use a custom image with pre-installed MSVC.
    # "windows-slave-1 windows-server-2012-r2-dc-v20160112-vs2015-cpp-python-msys windows-x86_64-1 europe-west1-d default windows-startup-script-ps1=jenkins-slave-windows.ps1"
    # "windows-slave-2 windows-server-2012-r2-dc-v20160112-vs2015-cpp-python-msys windows-x86_64-2 europe-west1-d default windows-startup-script-ps1=jenkins-slave-windows.ps1"
    "windows-slave-1 windows-server-2016-dc-bazel-ci-v20180115 windows-x86_64-1 europe-west1-d default windows-startup-script-ps1=jenkins-slave-windows-2016.ps1"
    "windows-slave-2 windows-server-2016-dc-bazel-ci-v20180115 windows-x86_64-2 europe-west1-d default windows-startup-script-ps1=jenkins-slave-windows-2016.ps1"
)

# Jenkins controller for ci.bazel.build
MASTER=(
    # VM name
    "jenkins"
    # Zone
    "europe-west1-d"
    # Metadata specification
    "google-container-manifest=jenkins.yml,startup-script=mount-volumes.sh"
    # Disk specification
    "name=jenkins-volumes-ssd,device-name=volumes"
    # Address name
    "ci"
    # Network name
    "default"
    # Instance group
    "ci-instance-group"
)

# Executor nodes for ci-staging.bazel.build
STAGING_SLAVES=(
    "ubuntu-14-04-slave-staging ubuntu-1404-lts ubuntu_14.04-x86_64-staging europe-west1-d staging startup-script=jenkins-slave.sh ubuntu-14-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-16-04-slave-staging ubuntu-1604-lts ubuntu_16.04-x86_64-staging europe-west1-d staging startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "ubuntu-docker-slave-staging ubuntu-1604-lts ubuntu_16.04-x86_64-docker-staging europe-west1-d default startup-script=jenkins-slave.sh ubuntu-16-04-slave.sh ubuntu-16-04-docker.sh bootstrap-bazel.sh linux-android.sh cleanup-install.sh"
    "freebsd-11-slave-staging https://www.googleapis.com/compute/v1/projects/freebsd-org-cloud-dev/global/images/freebsd-11-1-stable-amd64-2017-12-28 freebsd-11-staging europe-west1-d staging startup-script=jenkins-slave.sh freebsd-slave.sh freebsd-ci-homedir.sh"
    "freebsd-12-slave-staging https://www.googleapis.com/compute/v1/projects/freebsd-org-cloud-dev/global/images/freebsd-12-0-current-amd64-2017-12-28 freebsd-12-staging europe-west1-d staging startup-script=jenkins-slave.sh freebsd-slave.sh freebsd-ci-homedir.sh"
    # Fow Windows, we use a custom image with pre-installed MSVC.
    "windows-slave-staging windows-server-2012-r2-dc-v20160112-vs2015-cpp-python-msys windows-x86_64-staging europe-west1-d staging windows-startup-script-ps1=jenkins-slave-windows.ps1"
    # Remote Cache
    "remote-cache-staging ubuntu-1604-lts remote-cache-staging europe-west1-d staging startup-script=start-remote-cache.sh setup-remote-cache.sh"
)
STAGING_MASTER=(
    # VM name
    "jenkins-staging"
    # Zone
    "europe-west1-d"
    # Metadata specification
    "google-container-manifest=jenkins-staging.yml,startup-script=mount-volumes.sh"
    # Disk specification
    "name=jenkins-volumes-staging,device-name=volumes"
    # Address name
    "ci-staging"
    # Network name
    "staging"
    # Instance group
    "ci-staging-instance-group"
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
  local group="$7"

  gcloud compute instances create "$name" --tags jenkins \
      --zone "$location" --machine-type n1-standard-16 \
      --image-family container-vm --image-project google-containers \
      --metadata-from-file "$metadata" \
      --min-cpu-platform "Intel Skylake" \
      --boot-disk-type pd-ssd --boot-disk-size 250GB \
      --network "$network" \
      --address "$address" --disk "$disk"

  gcloud compute instance-groups unmanaged add-instances \
      "$group" --instances "$name" --zone "$location"
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

  if [[ $TAG == *-staging ]]; then
    MACHINE_TYPE="n1-standard-8"
    BOOT_DISK_SIZE="250GB"
  else
    MACHINE_TYPE="n1-standard-32"
    BOOT_DISK_SIZE="500GB"
  fi

  CPU_PLATFORM="Intel Skylake"
  if [[ $IMAGE == ubuntu-* ]]; then
    IMAGE_FLAG="--image-project=ubuntu-os-cloud --image-family=$IMAGE"
    LOCAL_SSD="--local-ssd interface=nvme"
  elif [[ $IMAGE == windows-server-2012-* ]]; then
    CPU_PLATFORM="Intel Haswell"
    MACHINE_TYPE="n1-standard-16"
    IMAGE_FLAG="--image $IMAGE"
    LOCAL_SSD=""
  else
    IMAGE_FLAG="--image $IMAGE"
    LOCAL_SSD="--local-ssd interface=scsi"
  fi

  gcloud compute instances create "$TAG" \
      --zone "$LOCATION" \
      --machine-type "$MACHINE_TYPE" \
      --network "$NETWORK" \
      $IMAGE_FLAG \
      --metadata-from-file "$STARTUP_METADATA" \
      --metadata jenkins_node="$JENKINS_NODE" \
      --min-cpu-platform "$CPU_PLATFORM" \
      --boot-disk-type pd-ssd --boot-disk-size "$BOOT_DISK_SIZE" \
      $LOCAL_SSD

  case "$TAG" in
    windows-*)
      # Nothing to do here.
      ;;

    freebsd*)
      # Wait a bit for the VM to fully start.
      wait_vm "$TAG" "$LOCATION" 120 /usr/bin/true

      # Install bash directly calling gcloud, as the ssh_command function
      # already depends on bash being installed and in PATH.
      gcloud compute ssh --zone="${LOCATION}" --command "sudo pkg install -y bash" "${TAG}"

      # Create the jenkins user, run additional set-up scripts and mark
      # the install process as finished.
      ssh_command "$TAG" "$LOCATION" \
          "pw useradd -n ci -s /usr/local/bin/bash -d /home/ci -m -w no" \
          "$@" \
          "echo \"echo -n '$JENKINS_NODE' >/home/ci/node_name\" | su -m ci"
      ;;

    *)
      # Wait a bit for the VM to fully start.
      wait_vm "$TAG" "$LOCATION"

      # Create the jenkins user, run additional set-up scripts and mark
      # the install process as finished.
      ssh_command "$TAG" "$LOCATION" \
          "sudo adduser --system --home /home/ci ci" \
          "$@" \
          "su ci -s /bin/bash -c \"echo -n '$JENKINS_NODE' >/home/ci/node_name\""
      ;;
  esac
}

# Updates the --metadata and --metadata-from-file values of an existing VM.
#
# Primary purpose is to propagate changes to the startup scripts (e.g.
# mount-volumes.sh for the jenkins controller, jenkins-slave.sh for Ubuntu nodes,
# etc.) without recreating the VM. The update needs a VM reboot to take effect.
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
      --metadata-from-file "$startup_metadata"
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

function print_vm_name() {
  echo $1
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
  "vms")
    action print_vm_name "$@"
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
    echo "ci-staging.bazel.build and ci.bazel.build." >&2
    exit 1
    ;;
esac
