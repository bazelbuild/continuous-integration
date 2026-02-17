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
from datetime import datetime
import os
import queue
import sys
import threading
import yaml

import gcloud

WORK_QUEUE = queue.Queue()


def worker():
    while True:
        item = WORK_QUEUE.get()
        if not item:
            break
        try:
            # We take a few keys out of the config item. The rest is passed
            # as-is to create_instance_template() and thus to the gcloud
            # command line tool.
            del item["count"]
            instance_group_name = item.pop("name")
            project = item.pop("project")
            zone = item.pop("zone", None)
            region = item.pop("region", None)
            del item["health_check"]
            del item["initial_delay"]

            if not project:
                raise Exception("Invalid instance config, no project name set")

            if not zone and not region:
                raise Exception("Invalid instance config, either zone or region must be specified")

            timestamp = datetime.now().strftime("%Y%m%dt%H%M%S")
            template_name = "{}-{}".format(instance_group_name, timestamp)

            # Create the new instance template.
            gcloud.create_instance_template(template_name, project=project, **item)
            print("Created instance template {}".format(template_name))
        finally:
            WORK_QUEUE.task_done()


def read_config_file():
    path = os.path.join(os.getcwd(), "instances.yml")
    with open(path, "rb") as fd:
        content = fd.read().decode("utf-8")
    return yaml.safe_load(content)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Bazel CI Instance Creation")
    parser.add_argument(
        "names",
        type=str,
        nargs="*",
        help="List of instance (group) names that should be created. "
        'These values must correspond to "name" entries in the '
        'Yaml configuration, e.g. "bk-docker".',
    )

    args = parser.parse_args(argv)
    config = read_config_file()

    # Verify names passed on the command-line.
    valid_names = [item["name"] for item in config["instance_groups"]]
    for name in args.names:
        if name not in valid_names:
            print("Unknown instance name: {}!".format(name))
            print("\nValid instance names are: {}".format(" ".join(valid_names)))
            return 1
    if not args.names:
        parser.print_help()
        print("\nValid instance names are: {}".format(" ".join(valid_names)))
        return 1

    # Put VM creation instructions into the work queue.
    for instance in config["instance_groups"]:
        if instance["name"] not in args.names:
            continue
        WORK_QUEUE.put({**config["default_vm"], **instance})

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


if __name__ == "__main__":
    sys.exit(main())
