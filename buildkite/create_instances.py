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

import argparse
import collections
import gcloud
import itertools
import os
import queue
import sys
import threading
import urllib.error
import urllib.request
import yaml


DEBUG = True

CONFIG_URL = 'https://github.com/bazelbuild/continuous-integration/blob/master/buildkite/instances.yml'
LOCAL_CONFIG_FILE_NAME = 'instances.yml'
DEFAULT_VM_CONFIG_KEY = 'default_vm'
INSTANCE_GROUPS_CONFIG_KEY = 'instance_groups'
SINGLE_INSTANCES_CONFIG_KEY = 'single_instances'

Config = collections.namedtuple('Config', ['default_vm', 'single_instances', 'instance_groups'])

class ConfigError(Exception):
    pass

PRINT_LOCK = threading.Lock()
WORK_QUEUE = queue.Queue()


def instance_group_task(instance_group_name, count, zone, **kwargs):
    template_name = instance_group_name + '-template'

    if gcloud.delete_instance_group(instance_group_name, zone=zone).returncode == 0:
        print('Deleted existing instance group: {}'.format(instance_group_name))

    if gcloud.delete_instance_template(template_name).returncode == 0:
        print('Deleted existing VM template: {}'.format(template_name))

    gcloud.create_instance_template(template_name, **kwargs)

    gcloud.create_instance_group(instance_group_name, zone=zone,
                                 base_instance_name=instance_group_name,
                                 template=template_name, size=count)


def single_instance_task(instance_name, zone, **kwargs):
    if gcloud.delete_instance(instance_name, zone=zone).returncode == 0:
        print('Deleted existing instance: {}'.format(instance_name))

    gcloud.create_instance(instance_name, zone=zone, **kwargs)


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


def get_config(use_local_config):
    config = read_config_file(use_local_config)
    return Config(default_vm=create_index(config, DEFAULT_VM_CONFIG_KEY),
                  single_instances=create_index(config, SINGLE_INSTANCES_CONFIG_KEY),
                  instance_groups=create_index(config, INSTANCE_GROUPS_CONFIG_KEY))


def read_config_file(use_local_config):
    content = None
    if use_local_config:
        path = os.path.join(os.getcwd(), LOCAL_CONFIG_FILE_NAME)
        try:
            with open(path, "r") as fd:
                content = fd.read()
        except IOError as ex:
            raise ConfigError('Cannot read local file %s: %s' % (path, ex))
    else:
        try:
            with urllib.request.urlopen(CONFIG_URL) as resp:
                reader = codecs.getreader("utf-8")
                content = reader(resp)
        except urllib.error.URLError as ex:
            raise ConfigError('Cannot read remote file %s: %s' % (CONFIG_URL, ex))

    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as ex:
        raise ConfigError('Malformed YAML: %s' % ex)


def create_index(config, key):
    if key not in config:
        raise ValueError('Missing entry "%s" from the configuration file.' % key)

    if not config[key]:
        return {}

    # Special case for Default VM: only one entry, so no need to create an index
    if isinstance(config[key], dict):
        return config[key]

    index = {}
    for item in config[key]:
        name = item.pop('name', None)
        if not name:
            raise ConfigError('At least one configuration entry for "%s" does not have a name.' % key)

        index[name] = item

    return index


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Bazel Continuous Integration Instance Creation")
    parser.add_argument('names', type=str, nargs='+',
                        help='List of instance (group) names that should be created. '
                             'These values must correspond to "name" entries in the '
                             'Yaml configuration, e.g. "bk-pipeline-ubuntu1804-java8".')
    parser.add_argument('--local_config', type=bool, default=False,
                        help='Whether to read the configuration from CWD/%s' % LOCAL_CONFIG_FILE_NAME)

    args = parser.parse_args(argv)

    try:
        config = get_config(args.local_config)
    except Exception as ex:
        print("Failed to retrieve configuration: %s" % ex)
        return 1

    # Put VM creation instructions into the work queue.
    for instance_group_name, params in config.instance_groups.items():
        if instance_group_name not in args.names:
            continue
        WORK_QUEUE.put({
            **config.default_vm,
            'instance_group_name': instance_group_name,
            **params
        })

    for instance_name, params in config.single_instances.items():
        if instance_name not in args.names:
            continue
        WORK_QUEUE.put({
            **config.default_vm,
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
