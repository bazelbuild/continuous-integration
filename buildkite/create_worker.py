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
import queue
import subprocess
import sys
import threading

DEBUG = True

LOCATION = 'europe-west1-d'

MACHINES = {
    'buildkite-ubuntu1404': {
        'count': 4,
        'startup_script': 'startup-ubuntu.sh',
        'machine_type': 'n1-standard-32',
        'local_ssd': 'interface=nvme',
    },
    'buildkite-ubuntu1604': {
        'count': 4,
        'startup_script': 'startup-ubuntu.sh',
        'machine_type': 'n1-standard-32',
        'local_ssd': 'interface=nvme',
    },
    'buildkite-windows': {
        'count': 4,
        'startup_script': 'startup-windows.ps1',
        'machine_type': 'n1-standard-32',
        'local_ssd': 'interface=scsi',
    },
    '%s-ubuntu1604' % getpass.getuser(): {
        'image': 'buildkite-ubuntu1604',
        'count': 4,
        'startup_script': 'startup-ubuntu.sh',
        'machine_type': 'n1-standard-32',
        'local_ssd': 'interface=nvme',
    }
}

PRINT_LOCK = threading.Lock()
WORK_QUEUE = queue.Queue()


def debug(*args, **kwargs):
    if DEBUG:
        with PRINT_LOCK:
            print(*args, **kwargs)


def run(args, **kwargs):
    debug('Running: %s' % ' '.join(args))
    return subprocess.run(args, **kwargs)


def delete_vm(vm):
    return run(['gcloud', 'compute', 'instances', 'delete', '--quiet', vm])


def create_vm(vm, idx, params):
    if idx > 0:
        vm = '%s-%s' % (vm, idx)
    image_family = params.get('image', vm)

    if delete_vm(vm).returncode == 0:
        with PRINT_LOCK:
            print('Deleted existing VM: %s' % vm)
    cmd = ['gcloud', 'compute', 'instances', 'create', vm]
    cmd.extend(['--zone', LOCATION])
    cmd.extend(['--machine-type', params['machine_type']])
    cmd.extend(['--network', 'buildkite'])
    if 'windows' in image_family:
        cmd.extend(['--metadata-from-file', 'windows-startup-script-ps1=' + params['startup_script']])
    else:
        cmd.extend(['--metadata-from-file', 'startup-script=' + params['startup_script']])
    cmd.extend(['--min-cpu-platform', 'Intel Skylake'])
    cmd.extend(['--boot-disk-type', 'pd-ssd'])
    cmd.extend(['--boot-disk-size', '50GB'])
    if 'local_ssd' in params:
        cmd.extend(['--local-ssd', params['local_ssd']])
    cmd.extend(['--image-project', 'bazel-public'])
    cmd.extend(['--image-family', image_family])
    cmd.extend(['--service-account', 'remote-account@bazel-public.iam.gserviceaccount.com'])
    cmd.extend(['--scopes', 'cloud-platform'])
    run(cmd)


def worker():
    while True:
        item = WORK_QUEUE.get()
        if not item:
            break
        try:
            create_vm(**item)
        finally:
            WORK_QUEUE.task_done()


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    # Put VM creation instructions into the work queue.
    worker_count = 0
    for vm, params in MACHINES.items():
        if argv and vm not in argv:
            continue
        worker_count += params['count']
        if params['count'] > 1:
            for idx in range(1, params['count'] + 1):
                WORK_QUEUE.put({
                    'vm': vm,
                    'idx': idx,
                    'params': params
                })
        else:
            WORK_QUEUE.put({
                'vm': vm,
                'idx': 0,
                'params': params
            })

    # Spawn worker threads that will create the VMs.
    threads = []
    for _ in range(worker_count):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    # Wait for all VMs to be created.
    WORK_QUEUE.join()

    # Signal worker threads to exit.
    for _ in range(worker_count):
        WORK_QUEUE.put(None)

    # Wait for worker threads to exit.
    for t in threads:
        t.join()

    return 0


if __name__ == '__main__':
    sys.exit(main())
