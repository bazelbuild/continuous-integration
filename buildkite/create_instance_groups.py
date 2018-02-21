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

import queue
import re
import subprocess
import sys
import threading

DEBUG = True

LOCATION = 'europe-west1-d'

AGENTS = {
    'buildkite-ubuntu1404': {
        'count': 8,
        'startup_script': 'startup-ubuntu.sh',
        'machine_type': 'n1-standard-32',
        'local_ssd': 'interface=nvme',
    },
    'buildkite-ubuntu1604': {
        'count': 8,
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
    'buildkite-freebsd11': {
        'count': 2,
        'startup_script': 'startup-ubuntu.sh',
        'machine_type': 'n1-standard-32',
        'local_ssd': 'interface=scsi',
    }
}

PRINT_LOCK = threading.Lock()
WORK_QUEUE = queue.Queue()


def debug(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


def run(args, **kwargs):
    debug('Running: %s' % ' '.join(args))
    return subprocess.run(args, **kwargs)


def delete_template(template_name):
    result = run(['gcloud', 'compute', 'instance-templates', 'delete', template_name, '--quiet'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    if result.returncode != 0:
        # It's not an error if 'delete' failed, because the template didn't exist in the first place.
        # But we do want to error out on other unexpected errors.
        if not re.search(r'The resource .* was not found', result.stdout):
            raise Exception('"gcloud compute instance-templates delete" returned unexpected error:\n%s' % result.stdout)
    return result


def create_template(template_name, image_family, params):
    cmd = ['gcloud', 'compute', 'instance-templates', 'create', template_name]
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


def delete_instance_group(group_name):
    result = run(['gcloud', 'compute', 'instance-groups', 'managed', 'delete', group_name, '--zone', LOCATION, '--quiet'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    if result.returncode != 0:
        # It's not an error if 'delete' failed, because the template didn't exist in the first place.
        # But we do want to error out on other unexpected errors.
        if not re.search(r'The resource .* was not found', result.stdout):
            raise Exception('"gcloud compute instance-groups managed delete" returned unexpected error:\n%s' % result.stdout)
    return result


def create_instance_group(group_name, template_name, count):
    return run(['gcloud', 'compute', 'instance-groups', 'managed', 'create', group_name, '--zone', LOCATION, '--base-instance-name', group_name, '--template', template_name, '--size', str(count)])


def workflow(image_family, params):
    template_name = image_family + '-template'
    group_name = image_family

    if delete_instance_group(group_name).returncode == 0:
        print('Deleted existing instance group: %s' % group_name)
    if delete_template(template_name).returncode == 0:
        print('Deleted existing VM template: %s' % template_name)
    create_template(template_name, image_family, params)
    create_instance_group(group_name, template_name, params['count'])


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
    for image_family, params in AGENTS.items():
        if argv and image_family not in argv:
            continue
        WORK_QUEUE.put({
            'image_family': image_family,
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
