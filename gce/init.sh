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

# Script to create the GCE setup for ci.bazel.build and ci-staging.bazel.build
# from scratch.
set -eu

# Each line contains: NAME NETWORK ADDRESS_NAME DISK_NAME restrict_http
SYSTEMS=(
  "prod default ci jenkins-volumes false"
  "staging staging ci-staging jenkins-volumes-staging true"
)

cd "$(dirname "${BASH_SOURCE[0]}")"

source utils/commands.sh
source utils/network.sh
source utils/create_disk.sh

function test_name() {
  local search="$1"
  local match="$2"
  if [ "$search" == "$match" ]; then
    return 0
  else
    return 1
  fi
}

function action() {
  local action=$1
  shift
  if (( $# == 0 )); then
    for i in "${SYSTEMS[@]}"; do
      $action $i
    done
  else
    local name="$1"
    shift
    for j in "${SYSTEMS[@]}"; do
      if test_name "$name" $j; then
        $action $j "$@"
      fi
    done
  fi
}

function create() {
  local name="$1"
  local network="$2"
  local ip_address="$3"
  local disk_name="$4"
  local restrict_http="$5"
  shift 5
  echo "[*] Creating disk ${disk_name}"
  create_disk "${disk_name}"
  echo "[*] Creating static IP address ${ip_address}"
  gcloud compute addresses create "${ip_address}"
  echo "[*] Creating cloud network ${network}"
  create_network "${network}"
  echo "[*] Setting-up firewall rules for ${network}"
  setup_firewall "${network}" "${restrict_http}" "${@}"
  echo "[*] Creating VMs for ${name}"
  ./vm.sh create "${name}"
}

function reset_firewall() {
  local name="$1"
  local network="$2"
  local ip_address="$3"
  local disk_name="$4"
  local restrict_http="$5"
  shift 5
  echo "[*] Setting-up firewall rules for ${network}"
  setup_firewall "${network}" "${restrict_http}" "${@}"
}

function usage() {
  echo "Usage: $0 (init|firewall) (staging|prod) [restricted_ip_ranges]" >&2
  exit 1
}

if (( $# < 2 )); then
  usage
fi

command="${1-}"
shift || true

case "${command}" in
  "init")
    echo "*** WARNING ***"
    echo "This is a risky operation as it will create ips and network without"
    echo "checking for its existence. It will also overwrite the firewall rules."
    echo -n "Are you sure you want to do that? [y/N] "
    read ans
    [ "$ans" = "y" ] || [ "$ans" = "Y" ] || exit 1
    action create "$@"
    ;;
  "firewall")
    action reset_firewall "$@"
    ;;
  *)
    usage
    ;;
esac
