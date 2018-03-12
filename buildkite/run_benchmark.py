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

import csv
import getpass
import json
import queue
import re
import subprocess
import sys
import os.path
import threading
import time
from uuid import uuid4

import gcloud
import gcloud_utils

DEBUG = True

CPU_PLATFORMS = {
    # 'europe-west1-b': ['Intel Sandy Bridge'],
    # 'europe-west1-c': ['Intel Ivy Bridge'],
    # 'europe-west1-d': ['Intel Broadwell', 'Intel Haswell', 'Intel Skylake'],
    'europe-west1-d': ['Intel Skylake'],
}
MACHINE_TYPES = [
    'n1-highmem-4',
    'n1-highmem-8',
    'n1-highmem-16',
    'n1-standard-32',
    # 'n1-standard-64'
]
IMAGES = ['buildkite-ubuntu1604']
#LOCAL_SSD = ['interface=nvme']
LOCAL_SSD = ['']
BOOT_DISK_SIZE = ['50GB']
REPEATS = 10

STARTUP_SCRIPT = 'startup-benchmark.sh'

PRINT_LOCK = threading.Lock()
WORK_QUEUE = queue.Queue()


def debug(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


def run(args, **kwargs):
    debug('Running: {}'.format(' '.join(args)))
    return subprocess.run(args, **kwargs)


def create_instance(instance_name, zone, cpu_platform, machine_type, image, local_ssd, boot_disk_size):
    image = {
        'boot_disk_size': boot_disk_size,
        'boot_disk_type': 'pd-ssd',
        'image_family': image,
        'image_project': 'bazel-public',
        'machine_type': machine_type,
        'metadata_from_file': 'startup-script=' + STARTUP_SCRIPT,
        'min_cpu_platform': cpu_platform,
        'network': 'buildkite',
        'scopes': 'cloud-platform',
        'service_account': 'remote-account@bazel-public.iam.gserviceaccount.com',
        'zone': zone,
    }
    if local_ssd:
        image['local_ssd'] = local_ssd
    gcloud.create_instance(instance_name, **image)


def fetch_benchmark_log(instance_name, zone):
    raw_log = gcloud.get_serial_port_output(instance_name, zone=zone).stdout
    filtered_log = gcloud_utils.prettify_logs(instance_name, raw_log, with_prefix=False)
    return '\n'.join(filtered_log)


def parse_benchmark_log(instance_name, zone, log):
    # The log contains the following marker lines:
    hardware_info_start = r"=== HARDWARE INFO START ==="
    hardware_info_end = r"=== HARDWARE INFO DONE ==="
    bazel_info_start = r"=== BAZEL INFO START @([\d.]+) ==="
    bazel_info_end = r"=== BAZEL INFO DONE @([\d.]+) ==="
    bazel_fetch_start = r"=== BAZEL FETCH START @([\d.]+) ==="
    bazel_fetch_end = r"=== BAZEL FETCH DONE @([\d.]+) ==="
    bazel_build_start = r"=== BAZEL BUILD START @([\d.]+) ==="
    bazel_build_end = r"=== BAZEL BUILD DONE @([\d.]+) ==="
    bazel_test_start = r"=== BAZEL TEST START @([\d.]+) ==="
    bazel_test_end = r"=== BAZEL TEST DONE @([\d.]+) ==="
    bazel_clean_start = r"=== BAZEL CLEAN START @([\d.]+) ==="
    bazel_clean_end = r"=== BAZEL CLEAN DONE @([\d.]+) ==="

    hardware_info = re.search(hardware_info_start + r'.*CPU_COUNT=(\d*).*RAM_GB=(\d*).*CPU_PLATFORM=(.*)' + hardware_info_end, log, re.DOTALL).groups()
    bazel_info = re.search(bazel_info_start + '(.*?)' + bazel_info_end, log, re.DOTALL).groups()
    bazel_fetch = re.search(bazel_fetch_start + '(.*?)' + bazel_fetch_end, log, re.DOTALL).groups()
    bazel_build = re.search(bazel_build_start + '(.*?)' + bazel_build_end, log, re.DOTALL).groups()
    bazel_test = re.search(bazel_test_start + '(.*?)' + bazel_test_end, log, re.DOTALL).groups()
    bazel_clean = re.search(bazel_clean_start + '(.*?)' + bazel_clean_end, log, re.DOTALL).groups()

    return {
        'timestamp': int(time.time()),
        'instance_name': instance_name,
        'zone': zone,
        'cpu_count': int(hardware_info[0]),
        'ram_gb': int(hardware_info[1]),
        'cpu_platform': hardware_info[2].strip(),
        'bazel_info': bazel_info[1].strip(),
        'bazel_info_duration_secs': float(bazel_info[2]) - float(bazel_info[0]),
        'bazel_fetch': bazel_fetch[1].strip(),
        'bazel_fetch_duration_secs': float(bazel_fetch[2]) - float(bazel_fetch[0]),
        'bazel_build_log': bazel_build[1].strip(),
        'bazel_build_duration_secs': float(bazel_build[2]) - float(bazel_build[0]),
        'bazel_test_log': bazel_test[1].strip(),
        'bazel_test_duration_secs': float(bazel_test[2]) - float(bazel_test[0]),
        'bazel_clean_log': bazel_clean[1].strip(),
        'bazel_clean_duration_secs': float(bazel_clean[2]) - float(bazel_clean[0]),
    }


def workflow(zone, cpu_platform, machine_type, image, local_ssd, boot_disk_size):
    instance_name = "benchmark-ubuntu-" + str(uuid4())
    try:
        # Create the VM.
        create_instance(instance_name, zone, cpu_platform, machine_type, image, local_ssd, boot_disk_size)

        # Wait for the VM to become ready.
        gcloud_utils.wait_for_instance(instance_name, zone=zone, status='RUNNING')

        # Wait for benchmark to complete.
        gcloud_utils.tail_serial_console(instance_name, zone=zone, until='=== BENCHMARK COMPLETE ===')

        log = fetch_benchmark_log(instance_name, zone)
        results = parse_benchmark_log(instance_name, zone, log)
        results['requested_cpu_platform'] = cpu_platform
        results['machine_type'] = machine_type
        results['image'] = image
        results['local_ssd'] = local_ssd
        results['boot_disk_size'] = boot_disk_size

        with open(os.path.join('results', instance_name + '.json'), 'w') as f:
            json.dump(results, f)

        with open(os.path.join('results', 'combined.csv'), 'a', newline='') as f:
            results_writer = csv.writer(f, )
            results_writer.writerow([
                results['timestamp'],
                results['instance_name'],
                results['zone'],
                results['cpu_count'],
                results['ram_gb'],
                results['requested_cpu_platform'],
                results['cpu_platform'],
                results['machine_type'],
                results['image'],
                results['local_ssd'],
                results['boot_disk_size'],
                "{0:.4f}".format(results['bazel_info_duration_secs']),
                "{0:.4f}".format(results['bazel_fetch_duration_secs']),
                "{0:.4f}".format(results['bazel_build_duration_secs']),
                "{0:.4f}".format(results['bazel_test_duration_secs']),
                "{0:.4f}".format(results['bazel_clean_duration_secs'])
            ])
    finally:
        try:
            gcloud.delete_instance(instance_name)
        except Exception:
            pass


def worker():
    while True:
        item = WORK_QUEUE.get()
        if not item:
            break
        try:
            workflow(**item)
        except Exception as e:
            print("Work {} failed with exception: {}".format(item, e))
        finally:
            WORK_QUEUE.task_done()


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    # Put VM creation instructions into the work queue.
    for zone, cpu_platforms in CPU_PLATFORMS.items():
        for cpu_platform in cpu_platforms:
            for machine_type in MACHINE_TYPES:
                for image in IMAGES:
                    for local_ssd in LOCAL_SSD:
                        for boot_disk_size in BOOT_DISK_SIZE:
                            for _ in range(REPEATS):
                                WORK_QUEUE.put({
                                    'zone': zone,
                                    'cpu_platform': cpu_platform,
                                    'machine_type': machine_type,
                                    'image': image,
                                    'local_ssd': local_ssd,
                                    'boot_disk_size': boot_disk_size
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
