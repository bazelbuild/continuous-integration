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
import subprocess
import sys
import threading

import gcloud


DEBUG = True

LOCATION = 'europe-west1-d'

# Note that the hostnames are parsed and trigger specific behavior for different use cases.
# The following parts have a special meaning:
#
# - "buildkite": This is a production VM running the Buildkite agent.
# - "pipeline": This is a special production VM that only runs pipeline setup
#               scripts.
# - "testing": This is a shared VM that can be used by project members for
#              experiments. It does not run the Buildkite agent.
# - "trusted": This is a special production VM that has additional access to
#              secrets.
# - "worker": This is a worker VM running normal CI jobs.
#
DEFAULT_VM = {
    'boot_disk_size': '50GB',
    'boot_disk_type': 'pd-ssd',
    'image_project': 'bazel-public',
    'machine_type': 'n1-standard-32',
    'min_cpu_platform': 'Intel Skylake',
    'network': 'buildkite',
    'scopes': 'cloud-platform',
    'service_account': 'remote-account@bazel-public.iam.gserviceaccount.com',
}

INSTANCE_GROUPS = {
    'buildkite-worker-ubuntu1404-java8': {
        'count': 4,
        'image_family': 'buildkite-worker-ubuntu1404-java8',
        'local_ssd': 'interface=nvme',
        'metadata_from_file': 'startup-script=startup-ubuntu.sh',
    },
    'buildkite-worker-ubuntu1604-java8': {
        'count': 4,
        'image_family': 'buildkite-worker-ubuntu1604-java8',
        'local_ssd': 'interface=nvme',
        'metadata_from_file': 'startup-script=startup-ubuntu.sh',
    },
    'buildkite-worker-ubuntu1804-nojava': {
        'count': 4,
        'image_family': 'buildkite-worker-ubuntu1804-nojava',
        'local_ssd': 'interface=nvme',
        'metadata_from_file': 'startup-script=startup-ubuntu.sh',
    },
    'buildkite-worker-ubuntu1804-java8': {
        'count': 8,
        'image_family': 'buildkite-worker-ubuntu1804-java8',
        'local_ssd': 'interface=nvme',
        'metadata_from_file': 'startup-script=startup-ubuntu.sh',
    },
    'buildkite-worker-ubuntu1804-java9': {
        'count': 8,
        'image_family': 'buildkite-worker-ubuntu1804-java9',
        'local_ssd': 'interface=nvme',
        'metadata_from_file': 'startup-script=startup-ubuntu.sh',
    },
    'buildkite-worker-ubuntu1804-java10': {
        'count': 8,
        'image_family': 'buildkite-worker-ubuntu1804-java10',
        'local_ssd': 'interface=nvme',
        'metadata_from_file': 'startup-script=startup-ubuntu.sh',
    },
    'buildkite-pipeline-ubuntu1804-java8': {
        'count': 1,
        'image_family': 'buildkite-pipeline-ubuntu1804-java8',
        'local_ssd': 'interface=nvme',
        'machine_type': 'n1-standard-8',
        'metadata_from_file': 'startup-script=startup-ubuntu.sh',
    },
    'buildkite-trusted-ubuntu1804-java8': {
        'count': 1,
        'image_family': 'buildkite-trusted-ubuntu1804-java8',
        'local_ssd': 'interface=nvme',
        'machine_type': 'n1-standard-8',
        'metadata_from_file': 'startup-script=startup-ubuntu.sh',
        'service_account': 'bazel-release-process@bazel-public.iam.gserviceaccount.com',
    },
    'buildkite-worker-windows-java8': {
        'count': 8,
        'image_family': 'buildkite-worker-windows-java8',
        'local_ssd': 'interface=scsi',
        'metadata_from_file': 'windows-startup-script-ps1=startup-windows.ps1',
    },
}

SINGLE_INSTANCES = {
    # 'testing-ubuntu1604-java8': {
    #     'image_family': 'buildkite-testing-ubuntu1604-java8',
    #     'metadata_from_file': 'startup-script=startup-ubuntu.sh',
    #     'disk': 'name={0},device-name={0},mode=rw,boot=no'.format('testing-ubuntu1604-persistent'),
    # },
    # 'testing-windows-java8': {
    #     'boot_disk_size': '500GB',
    #     'image_family': 'buildkite-testing-windows-java8',
    # },
}

PRINT_LOCK = threading.Lock()
WORK_QUEUE = queue.Queue()


def instance_group_task(instance_group_name, count, **kwargs):
    template_name = instance_group_name + '-template'

    if gcloud.delete_instance_group(instance_group_name, zone=LOCATION).returncode == 0:
        print('Deleted existing instance group: {}'.format(instance_group_name))

    if gcloud.delete_instance_template(template_name).returncode == 0:
        print('Deleted existing VM template: {}'.format(template_name))

    gcloud.create_instance_template(template_name, **kwargs)

    gcloud.create_instance_group(instance_group_name, zone=LOCATION,
                                 base_instance_name=instance_group_name,
                                 template=template_name, size=count)


def single_instance_task(instance_name, **kwargs):
    if gcloud.delete_instance(instance_name, zone=LOCATION).returncode == 0:
        print('Deleted existing instance: {}'.format(instance_name))

    gcloud.create_instance(instance_name, zone=LOCATION, **kwargs)


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
        WORK_QUEUE.put({
            **DEFAULT_VM,
            'instance_group_name': instance_group_name,
            **params
        })

    for instance_name, params in SINGLE_INSTANCES.items():
        # If the user specified instance (group) names on the command-line, we process only these
        # instances, otherwise we process all.
        if argv and instance_name not in argv:
            continue
        WORK_QUEUE.put({
            **DEFAULT_VM,
            'instance_name': instance_name,
            **params
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
