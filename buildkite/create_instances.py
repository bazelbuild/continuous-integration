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
import os
import queue
import sys
import threading
import urllib.error
import urllib.request
import yaml

import gcloud

CONFIG_URL = "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/instances.yml"
LOCAL_CONFIG_FILE_NAME = "instances.yml"

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
            count = item.pop("count")
            instance_group_name = item.pop("name")
            project = item.pop("project")
            zone = item.pop("zone", None)
            region = item.pop("region", None)

            if not project:
                raise Exception("Invalid instance config, no project name set")

            if not zone and not region:
                raise Exception(
                    "Invalid instance config, either zone or region must be specified"
                )

            template_name = instance_group_name + "-template"

            if zone is not None:
                if (gcloud.delete_instance_group(
                        instance_group_name, project=project,
                        zone=zone).returncode == 0):
                    print("Deleted existing instance group: {}".format(
                        instance_group_name))
            elif region is not None:
                if (gcloud.delete_instance_group(
                        instance_group_name, project=project,
                        region=region).returncode == 0):
                    print("Deleted existing instance group: {}".format(
                        instance_group_name))

            if gcloud.delete_instance_template(
                    template_name, project=project).returncode == 0:
                print("Deleted existing VM template: {}".format(template_name))

            gcloud.create_instance_template(
                template_name, project=project, **item)

            kwargs = {
                "project": project,
                "base_instance_name": instance_group_name,
                "size": count,
                "template": template_name,
            }
            if zone is not None:
                kwargs["zone"] = zone
            elif region is not None:
                kwargs["region"] = region
            gcloud.create_instance_group(instance_group_name, **kwargs)
        finally:
            WORK_QUEUE.task_done()


def read_config_file(use_local_config):
    content = None
    if use_local_config:
        path = os.path.join(os.getcwd(), LOCAL_CONFIG_FILE_NAME)
        with open(path, "rb") as fd:
            content = fd.read().decode("utf-8")
    else:
        with urllib.request.urlopen(CONFIG_URL) as resp:
            content = resp.read().decode("utf-8")
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
        'Yaml configuration, e.g. "bk-pipeline-ubuntu1804-java8".',
    )
    parser.add_argument(
        "--local_config",
        action="store_true",
        help="Whether to read the configuration from CWD/%s" %
        LOCAL_CONFIG_FILE_NAME,
    )

    args = parser.parse_args(argv)
    config = read_config_file(args.local_config)

    # Verify names passed on the command-line.
    valid_names = [item["name"] for item in config["instance_groups"]]
    for name in args.names:
        if name not in valid_names:
            print("Unknown instance name: {}!".format(name))
            print("\nValid instance names are: {}".format(
                " ".join(valid_names)))
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
