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

import collections
import re
import subprocess
import threading

DEBUG = True
PRINT_LOCK = threading.Lock()


def debug(*args, **kwargs):
    if DEBUG:
        with PRINT_LOCK:
            print(*args, **kwargs)


def is_sequence(seq):
  return isinstance(seq, collections.Sequence) and not isinstance(seq, str)


def gcloud(*args, **kwargs):
    cmd = ['gcloud']
    cmd += args
    for flag, value in kwargs.items():
        # Python uses underscores as word delimiters in kwargs, but gcloud wants dashes.
        flag = flag.replace('_', '-')
        if isinstance(value, bool):
            cmd += ['--' + ('no-' if not value else '') + flag]
        # We convert key=[a, b] into two flags: --key=a --key=b.
        elif is_sequence(value):
            for item in value:
                cmd += ['--' + flag, str(item)]
        else:
            cmd += ['--' + flag, str(value)]
    # Throws `subprocess.CalledProcessError` if the process exits with return code > 0.
    return subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, check=True)


def create_instance(name, **kwargs):
    try:
        return gcloud('compute', 'instances', 'create', name, **kwargs)
    except subprocess.CalledProcessError as e:
        raise Exception('"gcloud compute instance create" returned unexpected error:\n{}'.format(e.stderr))


def delete_instance(name, **kwargs):
    try:
        return gcloud('compute', 'instances', 'delete', name, '--quiet', **kwargs)
    except subprocess.CalledProcessError as e:
        # It's not an error if 'delete' failed, because the object didn't exist in the first place.
        # But we do want to error out on other unexpected errors.
        if not re.search(r'The resource .* was not found', e.stderr):
            raise Exception('"gcloud compute instance delete" returned unexpected error:\n{}'.format(e.stderr))
        return e


def describe_instance(name, **kwargs):
    try:
        return gcloud('compute', 'instances', 'describe', name, **kwargs)
    except subprocess.CalledProcessError as e:
        raise Exception('"gcloud compute instance describe" returned unexpected error:\n{}'.format(e.stderr))


def create_instance_group(name, **kwargs):
    try:
        return gcloud('compute', 'instance-groups', 'managed', 'create', name, **kwargs)
    except subprocess.CalledProcessError as e:
        raise Exception('"gcloud compute instance-groups managed create" returned unexpected error:\n{}'.format(e.stderr))


def delete_instance_group(name, **kwargs):
    try:
        return gcloud('compute', 'instance-groups', 'managed', 'delete', name, '--quiet', **kwargs)
    except subprocess.CalledProcessError as e:
        # It's not an error if 'delete' failed, because the object didn't exist in the first place.
        # But we do want to error out on other unexpected errors.
        if not re.search(r'The resource .* was not found', e.stderr):
            raise Exception('"gcloud compute instance-groups managed delete" returned unexpected error:\n{}'.format(e.stderr))
        return e


def create_instance_template(name, **kwargs):
    try:
        return gcloud('compute', 'instance-templates', 'create', name, **kwargs)
    except subprocess.CalledProcessError as e:
        raise Exception('"gcloud compute instance-templates create" returned unexpected error:\n{}'.format(e.stderr))


def delete_instance_template(name, **kwargs):
    try:
        return gcloud('compute', 'instance-templates', 'delete', name, '--quiet', **kwargs)
    except subprocess.CalledProcessError as e:
        # It's not an error if 'delete' failed, because the object didn't exist in the first place.
        # But we do want to error out on other unexpected errors.
        if not re.search(r'The resource .* was not found', e.stderr):
            raise Exception('"gcloud compute instance-templates delete" returned unexpected error:\n{}'.format(e.stderr))
        return e


def create_image(name, **kwargs):
    try:
        return gcloud('compute', 'images', 'create', name, **kwargs)
    except subprocess.CalledProcessError as e:
        raise Exception('"gcloud compute images create" returned unexpected error:\n{}'.format(e.stderr))


def reset_windows_password(name, **kwargs):
    try:
        return gcloud('compute', 'reset-windows-password', name, '--quiet', **kwargs)
    except subprocess.CalledProcessError as e:
        raise Exception('"gcloud compute reset-windows-password" returned unexpected error:\n{}'.format(e.stderr))


def get_serial_port_output(name, **kwargs):
    return gcloud('compute', 'instances', 'get-serial-port-output', name, **kwargs)
