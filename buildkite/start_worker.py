#!/usr/bin/env python3

import sys
import subprocess
import threading
import queue

DEBUG = True

LOCATION = 'europe-west1-d'

AGENTS = {
    "buildkite-ubuntu1404": {
        'count': 4,
        'startup_script': 'startup-ubuntu1404.sh',
        'machine_type': 'n1-standard-32',
        'local_ssd': 'interface=nvme',
    },
    "buildkite-ubuntu1604": {
        'count': 4,
        'startup_script': 'startup-ubuntu1604.sh',
        'machine_type': 'n1-standard-32',
        'local_ssd': 'interface=nvme',
    },
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


def create_vm(image_family, idx, params):
  vm = '%s-%s' % (image_family, idx)
  if delete_vm(vm).returncode == 0:
    with PRINT_LOCK:
      print("Deleted existing VM: %s" % vm)
  cmd = ['gcloud', 'compute', 'instances', 'create', vm]
  cmd.extend(['--zone', LOCATION])
  cmd.extend(['--machine-type', params['machine_type']])
  cmd.extend(['--network', 'buildkite'])
  if 'windows' in vm:
    cmd.extend(['--metadata-from-file', 'windows-startup-script-ps1=' + params['startup_script']])
  else:
    cmd.extend(['--metadata-from-file', 'startup-script=' + params['startup_script']])
  cmd.extend(['--min-cpu-platform', 'Intel Skylake'])
  cmd.extend(['--boot-disk-type', 'pd-ssd'])
  cmd.extend(['--boot-disk-size', '25GB'])
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
  for image_family, params in AGENTS.items():
    if argv and not image_family in argv:
      continue
    worker_count += params['count']
    for idx in range(1, params['count'] + 1):
      WORK_QUEUE.put({
          'image_family': image_family,
          'idx': idx,
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
