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

# This script defines functions to manipulate GCP networks.
set -eu

# Create a network $1
function create_network() {
  local name="$1"
  gcloud compute networks create "${name}" \
         --mode=legacy --range="192.168.59.0/24"
}

# Setup the firewall for network $1, allowing all ip ranges in ${3}..${$#}.
# If ${2} is set to true, HTTP request will also be restricted by these ranges.
# Each value in the list of ip ranges is a comma separated ip range, that will
# create a corresponding network rule.
function setup_firewall() {
  local network="$1"
  shift 1
  local restrict_http="${1:-false}"
  shift 1 || true
  local restrict_ips=("${@}")
  if (( $# == 0 )); then
    restrict_ips=("0.0.0.0/24")
  fi
  log "Removing all existing rules from network ${network}"
  local rules="$(gcloud compute firewall-rules list \
                | awk '$2 ~ /'"${network}"'/ {print $1}')"
  if [ -n "${rules}" ]; then
    gcloud compute firewall-rules delete ${rules}
  fi
  log "Allowing internal traffic inside network ${network}"
  gcloud compute firewall-rules create "${network}-allow-internal" \
    --network="${network}" --allow=tcp:0-65535,udp:0-65535,icmp \
    --source-ranges="192.168.0.0/16,172.16.0.0/12,10.0.0.0/8" \
    --description="Allow all TCP, UDP and ICMP traffic between machines on the '${network}' network"

  log "Enabling incoming HTTP traffic to the jenkins master for network ${network}"
  local counter=0
  if $restrict_http; then
    for i in "${restrict_ips[@]}"; do
      counter=$(($counter+1))
      gcloud compute firewall-rules create "${network}-allow-http-${counter}" \
        --network="${network}" \
        --allow=tcp:80,tcp:443 \
        --target-tags='jenkins' \
        --source-ranges=$i \
        --description='Allow HTTP(S) connection to Jenkins web interface'
    done
  else
    gcloud compute firewall-rules create "${network}-allow-http" \
      --network="${network}" \
      --allow=tcp:80,tcp:443 \
      --target-tags='jenkins' \
      --source-ranges=0.0.0.0/24 \
      --description='Allow HTTP(S) connection to Jenkins web interface'
  fi

  log "Enabling incoming SSH traffic to VMs for network ${network}"
  counter=0
  for i in "${restrict_ips[@]}"; do
    counter=$(($counter+1))
    gcloud compute firewall-rules create "${network}-allow-ssh-${counter}" \
      --network="${network}" \
      --allow=tcp:22 \
      --source-ranges=$i \
      --description='Allow SSH connections'
  done
}
