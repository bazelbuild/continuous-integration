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
import re
import subprocess
import sys
import threading

DEBUG = True

LOCATION = 'europe-west1-d'

INSTANCE_GROUPS = {
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
}

SINGLE_INSTANCES = {
    'buildkite-pipeline-ubuntu1604': {
        'startup_script': 'startup-ubuntu.sh',
        'machine_type': 'n1-standard-8',
        'persistent_disk': 'buildkite-pipeline-persistent'
    },
    '{}-ubuntu1604'.format(getpass.getuser()): {
        'image': 'buildkite-ubuntu1604',
        'startup_script': 'startup-ubuntu.sh',
        'machine_type': 'n1-standard-32',
        'local_ssd': 'interface=nvme',
    },
    '{}-windows'.format(getpass.getuser()): {
        'image': 'buildkite-windows',
        'startup_script': 'startup-windows.ps1',
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
    debug('Running: {}'.format(' '.join(args)))
    return subprocess.run(args, **kwargs)


def flags_for_instance(image_family, params):
    cmd = ['--machine-type', params['machine_type']]
    cmd.extend(['--network', 'buildkite'])
    if 'windows' in image_family:
        cmd.extend(['--metadata-from-file', 'windows-startup-script-ps1=' + params['startup_script']])
    else:
        cmd.extend(['--metadata-from-file', 'startup-script=' + params['startup_script']])
    cmd.extend(['--min-cpu-platform', 'Intel Skylake'])
    cmd.extend(['--boot-disk-type', 'pd-ssd'])
    cmd.extend(['--boot-disk-size', params.get('boot_disk_size', '50GB')])
    if 'local_ssd' in params:
        cmd.extend(['--local-ssd', params['local_ssd']])
    if 'persistent_disk' in params:
        cmd.extend(['--disk',
                    'name={0},device-name={0},mode=rw,boot=no'.format(params['persistent_disk'])])
    cmd.extend(['--image-project', 'bazel-public'])
    cmd.extend(['--image-family', image_family])
    cmd.extend(['--service-account', 'remote-account@bazel-public.iam.gserviceaccount.com'])
    cmd.extend(['--scopes', 'cloud-platform'])
    return cmd


def delete_instance_template(template_name):
    cmd = ['gcloud', 'compute', 'instance-templates', 'delete', template_name, '--quiet']
    result = run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    if result.returncode != 0:
        # It's not an error if 'delete' failed, because the template didn't exist in the first place.
        # But we do want to error out on other unexpected errors.
        if not re.search(r'The resource .* was not found', result.stdout):
            raise Exception('"gcloud compute instance-templates delete" returned unexpected error:\n{}'.format(result.stdout))
    return result


def create_instance_template(template_name, image_family, params):
    cmd = ['gcloud', 'compute', 'instance-templates', 'create', template_name]
    cmd.extend(flags_for_instance(image_family, params))
    run(cmd)


def delete_instance(instance_name):
    return run(['gcloud', 'compute', 'instances', 'delete', '--quiet', instance_name])


def create_instance(instance_name, image_family, params):
    cmd = ['gcloud', 'compute', 'instance', 'create', instance_name]
    cmd.extend(['--zone', LOCATION])
    cmd.extend(flags_for_instance(image_family, params))
    run(cmd)


def delete_instance_group(instance_group_name):
    cmd = ['gcloud', 'compute', 'instance-groups', 'managed', 'delete', instance_group_name]
    cmd.extend(['--zone', LOCATION])
    cmd.extend(['--quiet'])
    result = run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    if result.returncode != 0:
        # It's not an error if 'delete' failed, because the template didn't exist in the first place.
        # But we do want to error out on other unexpected errors.
        if not re.search(r'The resource .* was not found', result.stdout):
            raise Exception('"gcloud compute instance-groups managed delete" returned unexpected error:\n{}'.format(result.stdout))
    return result


def create_instance_group(instance_group_name, template_name, count):
    cmd = ['gcloud', 'compute', 'instance-groups', 'managed', 'create', instance_group_name]
    cmd.extend(['--zone', LOCATION])
    cmd.extend(['--base-instance-name', instance_group_name])
    cmd.extend(['--template', template_name])
    cmd.extend(['--size', str(count)])
    return run(cmd)


def instance_group_task(instance_group_name, params):
    image_family = params.get('image_family', instance_group_name)
    template_name = instance_group_name + '-template'

    if delete_instance_group(instance_group_name).returncode == 0:
        print('Deleted existing instance group: {}'.format(instance_group_name))
    if delete_instance_template(template_name).returncode == 0:
        print('Deleted existing VM template: {}'.format(template_name))
    create_instance_template(template_name, image_family, params)
    create_instance_group(instance_group_name, template_name, params['count'])


def single_instance_task(instance_name, params):
    image_family = params.get('image_family', instance_name)

    if delete_instance(instance_name).returncode == 0:
        print('Deleted existing instance: {}'.format(instance_name))
    create_instance(instance_name, image_family, params)


def worker():
    while True:
        item = WORK_QUEUE.get()
        if not item:
            break
        try:
            if 'instance_group_name' in item:
                instance_group_task(**item)
            elif 'instance_name' in item:
                single_instance_task(**item)
            else:
                raise Exception('Unknown task: {}'.format(item))
        finally:
            WORK_QUEUE.task_done()


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    # Put VM creation instructions into the work queue.
    for instance_group_name, params in INSTANCE_GROUPS.items():
        # If the user specified instance (group) names on the command-line, we process only these
        # instances, otherwise we process all.
        if argv and instance_group_name not in argv:
            continue
        # Do not automatically create user-specific instances. These must be specified explicitly
        # on the command-line.
        if instance_group_name.startswith(getpass.getuser()) and instance_group_name not in argv:
            continue
        WORK_QUEUE.put({
            'instance_group_name': instance_group_name,
            'params': params
        })

    for instance_name, params in SINGLE_INSTANCES.items():
        if argv and instance_name not in argv:
            continue
        if instance_name.startswith(getpass.getuser()) and instance_name not in argv:
            continue
        WORK_QUEUE.put({
            'instance_name': instance_name,
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
