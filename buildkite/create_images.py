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

import getpass
import json
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from datetime import datetime

DEBUG = False

LOCATION = 'europe-west1-d'

IMAGE_CREATION_VMS = {
    # Find the newest FreeBSD 11 image via:
    # gcloud compute images list --project freebsd-org-cloud-dev \
    #     --no-standard-images
    # 'buildkite-freebsd11': {
    #     'source_image': 'https://www.googleapis.com/compute/v1/projects/freebsd-org-cloud-dev/global/images/freebsd-11-1-stable-amd64-2017-12-28',
    #     'target_image_family': 'bazel-freebsd11',
    #     'scripts': [
    #         'setup-freebsd.sh',
    #         'install-buildkite-agent.sh'
    #     ]
    # },
    'buildkite-ubuntu1404': {
        'source_image_project': 'ubuntu-os-cloud',
        'source_image_family': 'ubuntu-1404-lts',
        'target_image_family': 'buildkite-ubuntu1404',
        'scripts': [
            'shell-utils.sh',
            'setup-ubuntu.sh',
            'install-azul-zulu.sh',
            'install-bazel.sh',
            'install-buildkite-agent.sh',
            'install-docker.sh',
            'install-nodejs.sh',
            'install-python36.sh',
            'install-android-sdk.sh',
            'shutdown.sh'
        ],
        'licenses': [
            'https://www.googleapis.com/compute/v1/projects/vm-options/global/licenses/enable-vmx'
        ]
    },
    'buildkite-ubuntu1604': {
        'source_image_project': 'ubuntu-os-cloud',
        'source_image_family': 'ubuntu-1604-lts',
        'target_image_family': 'buildkite-ubuntu1604',
        'scripts': [
            'shell-utils.sh',
            'setup-ubuntu.sh',
            'install-azul-zulu.sh',
            'install-bazel.sh',
            'install-buildkite-agent.sh',
            'install-docker.sh',
            'install-nodejs.sh',
            'install-python36.sh',
            'install-android-sdk.sh',
            'shutdown.sh'
        ],
        'licenses': [
            'https://www.googleapis.com/compute/v1/projects/vm-options/global/licenses/enable-vmx'
        ]
    },
    # 'buildkite-windows2016': {
    #     'source_image_project': 'windows-cloud',
    #     'source_image_family': 'windows-2016',
    #     'target_image_family': 'buildkite-windows2016',
    #     'scripts': [
    #         'setup-windows2016.ps1'
    #     ]
    # }
    'buildkite-windows': {
        'source_image_project': 'windows-cloud',
        'source_image_family': 'windows-1709-core',
        'target_image_family': 'buildkite-windows',
        'scripts': [
            'setup-windows-manual.ps1'
        ]
    }
}

MY_IPV4 = urllib.request.urlopen('https://v4.ifconfig.co/ip').read().decode('us-ascii').strip()
# MY_IPV4 = urllib.request.urlopen('https://v4.ident.me').read().decode('us-ascii').strip()

PRINT_LOCK = threading.Lock()
WORK_QUEUE = queue.Queue()


def debug(*args, **kwargs):
    if DEBUG:
        with PRINT_LOCK:
            print(*args, **kwargs)


def run(args, **kwargs):
    debug('Running: %s' % ' '.join(args))
    return subprocess.run(args, **kwargs)


def wait_for_vm(vm, status):
    while True:
        result = run(['gcloud', 'compute', 'instances', 'describe', '--zone', LOCATION,
                      '--format', 'json', vm], check=True, stdout=subprocess.PIPE)
        current_status = json.loads(result.stdout)['status']
        if current_status == status:
            debug("wait_for_vm: VM %s reached status %s" % (vm, status))
            break
        else:
            debug("wait_for_vm: Waiting for VM %s to transition from status %s -> %s" %
                  (vm, current_status, status))
        time.sleep(1)


def print_pretty_logs(vm, log):
    with PRINT_LOCK:
        for line in log.splitlines():
            # Skip empty lines.
            if not line:
                continue
            if 'ubuntu' in vm:
                match = re.match(r'.*INFO startup-script: (.*)', line)
                if match:
                    print("%s: %s" % (vm, match.group(1)))
            # elif 'windows' in vm:
            #     match = re.match(r'.*windows-startup-script-ps1: (.*)', line)
            #     if match:
            #         print(match.group(1))
            else:
                print("%s: %s" % (vm, line))


def tail_serial_console(vm, start=None, until=None):
    next_start = start if start else '0'
    while True:
        result = run(['gcloud', 'compute', 'instances', 'get-serial-port-output', '--zone', LOCATION, '--start',
                      next_start, vm], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if result.returncode != 0:
            break
        print_pretty_logs(vm, result.stdout)
        next_start = re.search(r'--start=(\d*)', result.stderr).group(1)
        if until and until in result.stdout:
            break
    return next_start


def merge_setup_scripts(scripts):
    # Merge all setup scripts into one.
    merged_script_path = tempfile.mkstemp()[1]
    with open(merged_script_path, 'w') as merged_script_file:
        for script in scripts:
            with open(script, 'r') as script_file:
                merged_script_file.write(script_file.read() + '\n')
    return merged_script_path


def create_vm(vm, params):
    merged_script_path = merge_setup_scripts(params['scripts'])
    try:
        cmd = ['gcloud', 'compute', 'instances', 'create', vm]
        cmd.extend(['--zone', LOCATION])
        cmd.extend(['--machine-type', 'n1-standard-8'])
        cmd.extend(['--network', 'buildkite'])
        if 'windows' in vm:
            cmd.extend(['--metadata-from-file', 'windows-startup-script-ps1=' + merged_script_path])
        else:
            cmd.extend(['--metadata-from-file', 'startup-script=' + merged_script_path])
        cmd.extend(['--min-cpu-platform', 'Intel Skylake'])
        cmd.extend(['--boot-disk-type', 'pd-ssd'])
        cmd.extend(['--boot-disk-size', '50GB'])
        if 'source_image' in params:
            cmd.extend(['--image', params['source_image']])
        else:
            cmd.extend(['--image-project', params['source_image_project']])
            cmd.extend(['--image-family', params['source_image_family']])
        run(cmd)
    finally:
        os.remove(merged_script_path)


def delete_vm(vm):
    run(['gcloud', 'compute', 'instances', 'delete', '--quiet', vm])


def create_image(vm, params):
    cmd = ['gcloud', 'compute', 'images', 'create', vm]
    cmd.extend(['--family', params['target_image_family']])
    cmd.extend(['--source-disk', vm])
    cmd.extend(['--source-disk-zone', LOCATION])
    for license in params.get('licenses', []):
        cmd.extend(['--licenses', license])
    run(cmd)


# https://stackoverflow.com/a/25802742
def write_to_clipboard(output):
    process = subprocess.Popen(
        'pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
    process.communicate(output.encode('utf-8'))


def print_windows_instructions(vm):
    tail_start = tail_serial_console(vm, until='Finished running startup scripts')

    pw = json.loads(run(['gcloud', 'compute', 'reset-windows-password', '--format', 'json', '--quiet',
                         vm], check=True, stdout=subprocess.PIPE).stdout)
    rdp_file = tempfile.mkstemp(suffix='.rdp')[1]
    with open(rdp_file, 'w') as f:
        f.write('full address:s:' + pw['ip_address'] + '\n')
        f.write('username:s:' + pw['username'] + '\n')
    run(['open', rdp_file])
    write_to_clipboard(pw['password'])
    with PRINT_LOCK:
        print('Use this password to connect to the Windows VM: ' + pw['password'])
        print('Please run the setup script C:\\setup.ps1 once you\'re logged in.')

    # Wait until the VM reboots once, then open RDP again.
    tail_start = tail_serial_console(vm, start=tail_start, until='Finished running startup scripts')
    print('Connecting via RDP a second time to finish the setup...')
    write_to_clipboard(pw['password'])
    run(['open', rdp_file])
    return tail_start


def workflow(name, params):
    vm = "%s-image-%s" % (name, int(datetime.now().timestamp()))
    try:
        # Create the VM.
        create_vm(vm, params)

        # Wait for the VM to become ready.
        wait_for_vm(vm, 'RUNNING')

        if 'windows' in vm:
            # Wait for VM to be ready, then print setup instructions.
            tail_start = print_windows_instructions(vm)
            # Continue printing the serial console until the VM shuts down.
            tail_serial_console(vm, start=tail_start)
        else:
            # Continuously print the serial console.
            tail_serial_console(vm)

        # Wait for the VM to completely shutdown.
        wait_for_vm(vm, 'TERMINATED')

        # Create a new image from our VM.
        create_image(vm, params)
    finally:
        delete_vm(vm)


def worker():
    while True:
        item = WORK_QUEUE.get()
        if not item:
            break
        try:
            workflow(**item)
        finally:
            WORK_QUEUE.task_done()


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    # Put VM creation instructions into the work queue.
    for name, params in IMAGE_CREATION_VMS.items():
        if argv and name not in argv:
            continue
        WORK_QUEUE.put({
            'name': name,
            'params': params
        })

    # Spawn worker threads that will create the VMs.
    threads = []
    for _ in range(WORK_QUEUE.qsize()):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    # Wait for all VMs to be created.
    WORK_QUEUE.join()

    # Signal worker threads to exit.
    for _ in range(len(threads)):
        WORK_QUEUE.put(None)

    # Wait for worker threads to exit.
    for t in threads:
        t.join()

    return 0


if __name__ == '__main__':
    sys.exit(main())
