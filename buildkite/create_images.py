#!/usr/bin/env python3

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime

DEBUG = False

LOCATION = 'europe-west1-d'

IMAGE_CREATION_VMS = {
    # 'buildkite-freebsd11-image': {
    #     'source_image': 'https://www.googleapis.com/compute/v1/projects/freebsd-org-cloud-dev/global/images/freebsd-11-1-stable-amd64-2017-12-28',
    #     'target_image_family': 'bazel-freebsd11',
    #     'scripts': [
    #         'setup-freebsd.sh',
    #         'install-buildkite-agent.sh'
    #     ]
    # },
    'buildkite-ubuntu1404-image': {
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
            'install-android-sdk.sh',
            'shutdown.sh'
        ]
    },
    'buildkite-ubuntu1604-image': {
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
            'install-android-sdk.sh',
            'shutdown.sh'
        ]
    },
    # 'buildkite-windows2016-image': {
    #     'source_image_project': 'windows-cloud',
    #     'source_image_family': 'windows-2016',
    #     'target_image_family': 'bazel-windows2016',
    #     'scripts': [
    #         'setup-windows2016.ps1'
    #     ]
    # }
}


def debug(*args, **kwargs):
  if DEBUG:
    print(*args, **kwargs)


def run(args, **kwargs):
  if DEBUG:
    print('Running: %s' % ' '.join(args))
  return subprocess.run(args, **kwargs)


def wait_for_vm(vm, status):
  while True:
    result = run(['gcloud', 'compute', 'instances', 'describe', '--zone', LOCATION, '--format', 'json', vm], check=True, stdout=subprocess.PIPE)
    current_status = json.loads(result.stdout)['status']
    if current_status == status:
      debug("wait_for_vm: VM %s reached status %s" % (vm, status))
      break
    else:
      debug("wait_for_vm: Waiting for VM %s to transition from status %s -> %s" % (vm, current_status, status))
    time.sleep(1)


def print_pretty_logs(vm, log):
  for line in log.splitlines():
    # Skip empty lines.
    if not line:
      continue
    if 'ubuntu' in vm:
      match = re.match(r'.*INFO startup-script: (.*)', line)
      if match:
        print(match.group(1))
    elif 'windows' in vm:
      match = re.match(r'.*windows-startup-script-ps1: (.*)', line)
      if match:
        print(match.group(1))
    else:
      print(line)


def tail_serial_console(vm):
  next_start = '0'
  while True:
    result = run(['gcloud', 'compute', 'instances', 'get-serial-port-output', '--zone', LOCATION, '--start', next_start, vm], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if result.returncode != 0:
      break
    print_pretty_logs(vm, result.stdout)
    next_start = re.search(r'--start=(\d*)', result.stderr).group(1)


def merge_setup_scripts(scripts):
  # Merge all setup scripts into one.
  merged_script_path = tempfile.mkstemp()[1]
  with open(merged_script_path, 'w') as merged_script_file:
    for script in scripts:
      with open(script, 'r') as script_file:
        script_contents = script_file.read()
        script_contents.replace('BUILDKITE_TOKEN="xxx"', 'BUILDKITE_TOKEN="%s"' % os.environ['BUILDKITE_TOKEN'])
        merged_script_file.write(script_contents + '\n')
  return merged_script_path


def create_vm(vm, params):
  merged_script_path = merge_setup_scripts(params['scripts'])
  try:
    cmd = ['gcloud', 'compute', 'instances', 'create', vm]
    cmd.extend(['--zone', LOCATION])
    cmd.extend(['--machine-type', 'n1-standard-32'])
    cmd.extend(['--network', 'buildkite'])
    if 'windows' in vm:
      cmd.extend(['--metadata-from-file', 'windows-startup-script-ps1=' + merged_script_path])
    else:
      cmd.extend(['--metadata-from-file', 'startup-script=' + merged_script_path])
    cmd.extend(['--min-cpu-platform', 'Intel Skylake'])
    cmd.extend(['--boot-disk-type', 'pd-ssd'])
    cmd.extend(['--boot-disk-size', '25GB'])
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


def create_image(vm, target_image_family):
  run(['gcloud', 'compute', 'images', 'create', vm, '--family', target_image_family, '--source-disk', vm, '--source-disk-zone', LOCATION])


def main(argv=None):
  if argv is None:
    argv = sys.argv[1:]

  if not 'BUILDKITE_TOKEN' in os.environ:
    print("Please set the BUILDKITE_TOKEN environment variable.")
    print("You can get the token from: https://buildkite.com/organizations/bazel/agents")
    return 1

  for vm, params in IMAGE_CREATION_VMS.items():
    if argv and not vm in argv:
        continue
    vm = "%s-%s" % (vm, int(datetime.now().timestamp()))
    try:
      # Create the VM.
      create_vm(vm, params)

      # Wait for the VM to become ready.
      wait_for_vm(vm, 'RUNNING')

      # Continuously print the serial console.
      tail_serial_console(vm)

      # Wait for the VM to shutdown.
      wait_for_vm(vm, 'TERMINATED')

      # Create a new image from our VM.
      create_image(vm, params['target_image_family'])
    finally:
      delete_vm(vm)
  return 0

if __name__ == '__main__':
  sys.exit(main())
