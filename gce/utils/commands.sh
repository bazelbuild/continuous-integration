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

# Some common methods to talk to GCE
set -eu

# Print a log message if VERBOSE is set to true
function _log() {
  echo "[$(basename "$0"):${FUNCNAME[2]}:${BASH_LINENO[1]}]" "$@"
}
function log() {
  if [ "${VERBOSE-}" = yes ]; then
    echo -n "INFO: "
    _log "$@"
  fi
}

# Test whether $1 is the name of an existing instance on GCE
function test_vm() {
  (( $(gcloud compute instances list "$1" | wc -l) > 1 ))
}

# Wait for a VM $1 in zone $2 to be up and running using ssh.
# This function will wait for at most $3 seconds.
function wait_vm() {
  local vm="$1"
  local zone="$2"
  local timeout="${3-60}"  # Wait for 1 minute maximum by default
  local starttime="$(date +%s)"
  while (( "$(date +%s)" - "$starttime" < "$timeout" )); do
    # gcloud compute ssh forward the return code of the executed command.
    if gcloud compute ssh --zone="$zone" --command /bin/true "$vm" &>/dev/null
    then
      return 0
    fi
  done
  return 1
}

# SSH to a VM $1 on zone  $2 and execute the command giving by the rest of
# the arguments.
function ssh_command() {
  local TAG="$1"
  local LOCATION="$2"
  local tmpdir="${TMPDIR:-/tmp}"
  # ${tmp} points to a file containing the list of commands to execute.
  local tmp="$(mktemp ${tmpdir%%/}/vm-ssh.XXXXXXXX)"
  trap "rm -f ${tmp}" EXIT
  shift 2
  # Truncate the list of commands
  echo -n >"${tmp}"
  # And then add the commands provided as argument.
  for i in "$@"; do
    if [ -f "$i" ]; then
      cat "$i" >>"${tmp}"
    else
      echo "$i" >>"${tmp}"
    fi
  done
  cat "${tmp}" | gcloud compute ssh --zone="${LOCATION}" \
      --command "cat >/tmp/s.sh; sudo bash /tmp/s.sh; rm /tmp/s.sh" \
      "${TAG}"
  rm -f "${tmp}"
  trap - EXIT
}
