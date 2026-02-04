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
from concurrent import futures
from datetime import datetime
import multiprocessing
import os
import sys
from typing import Any, Dict, List, Optional, Sequence
import yaml

import gcloud


def create_instance_group(config: Dict[str, Any]) -> int:
    instance_group_name: str = ""
    try:
        # We take a few keys out of the config. The rest is passed
        # as-is to create_instance_template() and thus to the gcloud
        # command line tool.
        count = config.pop("count")
        instance_group_name = config.pop("name")
        project = config.pop("project")
        zone = config.pop("zone", None)
        region = config.pop("region", None)
        health_check = config.pop("health_check", None)
        initial_delay = config.pop("initial_delay", None)

        if not project:
            raise Exception("Invalid instance config, no project name set")

        if not zone and not region:
            raise Exception("Invalid instance config, either zone or region must be specified")

        timestamp = datetime.now().strftime("%Y%m%dt%H%M%S")
        template_name = "{}-{}".format(instance_group_name, timestamp)

        if zone is not None:
            res = gcloud.delete_instance_group(
                    instance_group_name, project=project, zone=zone
                )
            if hasattr(res, 'returncode') and res.returncode == 0:
                print(f"Deleted existing instance group: {instance_group_name}")
        elif region is not None:
            res = gcloud.delete_instance_group(
                    instance_group_name, project=project, region=region
                )
            if hasattr(res, 'returncode') and res.returncode == 0:
                print(f"Deleted existing instance group: {instance_group_name}")

        # Create the new instance template.
        gcloud.create_instance_template(template_name, project=project, **config)
        print(f"Created instance template {template_name}")

        # Create instance groups with the new template.
        kwargs: Dict[str, Any] = {
            "project": project,
            "base_instance_name": instance_group_name,
            "size": count,
            "template": template_name,
        }
        if zone:
            kwargs["zone"] = zone
        elif region:
            kwargs["region"] = region
        if health_check:
            kwargs["health_check"] = health_check
        if initial_delay:
            kwargs["initial_delay"] = initial_delay
        gcloud.create_instance_group(instance_group_name, **kwargs)
        print(f"Created instance group {instance_group_name}")
        return 0
    except Exception as ex:
        print(f"Failed to create {instance_group_name}: {ex}", file=sys.stderr)
        return 1


def read_config_file() -> Any:
    path = os.path.join(os.getcwd(), "instances.yml")
    with open(path, "rb") as fd:
        content = fd.read().decode("utf-8")
    return yaml.safe_load(content)


def main(argv: Optional[List[str]] = None) -> int:
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
    valid_names = [item["name"] for item in config["instance_groups"]]

    if not args.names:
        parser.print_help()
        print("\nValid instance names are: {}".format(" ".join(valid_names)))
        return 1

    # Handle multiple args as well as a single-arg comma-delimited list.
    names = args.names if len(args.names) > 1 else args.names[0].split(",")

    # Verify names passed on the command-line.
    for name in names:
        if name not in valid_names:
            print("Unknown instance name: {}!".format(name))
            print("\nValid instance names are: {}".format(" ".join(valid_names)))
            return 1

    selected_instances = [i for i in config["instance_groups"] if i["name"] in names]

    # Mimic v3.5 default of
    # https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor
    max_workers = multiprocessing.cpu_count() * 5
    with futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        tasks = [
            pool.submit(create_instance_group, config={**config["default_vm"], **i})
            for i in selected_instances
        ]
        return max(list(t.result() for t in futures.as_completed(tasks)))


if __name__ == "__main__":
    sys.exit(main())
