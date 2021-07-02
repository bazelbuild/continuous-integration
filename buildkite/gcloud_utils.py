#!/usr/bin/env python3
#
# Copyright 2018 The Bazel Authors. All rights reserved.
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

import gcloud
import json
import subprocess
import time
import re


def wait_for_instance(instance_name, project, zone, status):
    while True:
        result = gcloud.describe_instance(instance_name, project=project, zone=zone, format="json")
        current_status = json.loads(result.stdout)["status"]
        if current_status == status:
            gcloud.debug(
                "wait_for_instance: {}/{} arrived at status {}".format(zone, instance_name, status)
            )
            break
        else:
            gcloud.debug(
                "wait_for_instance: Waiting for {}/{} to go from status {} to status {}".format(
                    zone, instance_name, current_status, status
                )
            )
        time.sleep(5)


def prettify_logs(instance_name, log, with_prefix=True):
    for line in log.splitlines():
        # Skip empty lines.
        if not line:
            continue

        # Filter for log lines printed by our startup script, ignore the rest.
        # Then drop the common prefix to make the output easier to read.
        # For unknown platforms, we just take every line unmodified.
        if "ubuntu" in instance_name or "docker" in instance_name:
            match = re.match(r".*GCEMetadataScripts: startup-script: (.*)", line)
            if not match:
                continue
            line = match.group(1)
        elif "windows" in instance_name:
            match = re.match(r".*windows-startup-script-ps1: (.*)", line)
            if not match:
                continue
            line = match.group(1)

        if with_prefix:
            yield "{}: {}".format(instance_name, line)
        else:
            yield line


def print_pretty_logs(instance_name, log):
    lines = ("\n".join(prettify_logs(instance_name, log))).strip()
    if lines:
        with gcloud.PRINT_LOCK:
            print(lines)


def tail_serial_console(instance_name, project, zone, start=None, until=None):
    next_start = start if start else "0"
    while True:
        try:
            result = gcloud.get_serial_port_output(
                instance_name, project=project, zone=zone, start=next_start
            )
        except subprocess.CalledProcessError as e:
            if "Could not fetch serial port output: TIMEOUT" in e.stderr:
                gcloud.debug("tail_serial_console: Retrying after TIMEOUT")
                continue
            gcloud.debug("tail_serial_console: Done, because got exception: {}".format(e))
            if e.stdout:
                gcloud.debug("stdout: " + e.stdout)
            if e.stderr:
                gcloud.debug("stderr: " + e.stderr)
            break
        print_pretty_logs(instance_name, result.stdout)
        next_start = re.search(r"--start=(\d*)", result.stderr).group(1)
        if until and until in result.stdout:
            gcloud.debug('tail_serial_console: Done, because found string "{}"'.format(until))
            break
        time.sleep(5)
    return next_start
