#!/usr/bin/env python3
#
# Copyright 2026 The Bazel Authors. All rights reserved.
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
import sys
import yaml

import gcloud


def reconcile_reservation(config, plan=False):
    reservation_name = config.pop("name")
    project = config.pop("project", None)
    zone = config.pop("zone", None)
    machine_type = config.pop("machine_type", None)
    count = config.pop("count", None)
    description = config.pop("description", None)

    summary = {
        "name": reservation_name or "-",
        "project": project or "-",
        "zone": zone or "-",
        "machine_type": machine_type or "-",
        "current_count": "-",
        "desired_count": str(count) if count is not None else "-",
        "action": "error",
    }

    try:
        if not project or not zone or not machine_type:
            raise Exception("Invalid reservation config: project, zone, and machine_type are required")
        if count is None or int(count) <= 0:
            raise Exception("Invalid reservation config: count must be a positive integer")

        count = int(count)
        existing = gcloud.describe_reservation(reservation_name, project=project, zone=zone)

        if existing is None:
            if not plan:
                create_kwargs = {
                    "project": project,
                    "zone": zone,
                    "machine_type": machine_type,
                    "vm_count": count,
                }
                if description:
                    create_kwargs["description"] = description
                create_kwargs.update(config)
                gcloud.create_reservation(reservation_name, **create_kwargs)
            summary["action"] = "create (plan)" if plan else "created"
        else:
            spec = existing.get("specificReservation", {})
            existing_machine_type = (
                spec.get("instanceProperties", {}).get("machineType", "").split("/")[-1]
            )
            existing_count = int(spec.get("count", 0))
            summary["current_count"] = str(existing_count)

            if existing_machine_type != machine_type:
                raise Exception(
                    f"Reservation {reservation_name} in {project}/{zone} has machine_type "
                    f"'{existing_machine_type}', but config specifies '{machine_type}'. "
                    f"GCE cannot change a reservation's machine type in place; "
                    f"delete the existing reservation first so it can be recreated."
                )

            if existing_count != count:
                if not plan:
                    gcloud.update_reservation(
                        reservation_name, project=project, zone=zone, vm_count=count
                    )
                summary["action"] = (
                    f"update {existing_count} -> {count} (plan)"
                    if plan
                    else f"updated ({existing_count} -> {count})"
                )
            else:
                summary["action"] = "no-op"
    except Exception as ex:
        print(f"Failed to reconcile reservation {reservation_name}: {ex}", file=sys.stderr)

    return summary


def print_summary_table(results):
    headers = ("NAME", "PROJECT", "ZONE", "MACHINE_TYPE", "CURRENT", "DESIRED", "ACTION")
    rows = [tuple(r.values()) for r in results]
    widths = [max(len(val) for val in col) for col in zip(headers, *rows)]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print("\n" + fmt.format(*headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(fmt.format(*row))


def read_config_file():
    path = os.path.join(os.getcwd(), "reservations.yml")
    with open(path, "rb") as fd:
        content = fd.read().decode("utf-8")
    return yaml.safe_load(content)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Bazel CI GCE Reservation Management")
    parser.add_argument(
        "names",
        type=str,
        nargs="*",
        help="List of reservation names to reconcile. "
        'These values must correspond to "name" entries in '
        "reservations.yml. If omitted, all reservations in "
        "reservations.yml are reconciled.",
    )
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Check existing reservations and print planned changes in a summary table without mutating anything.",
    )
    args = parser.parse_args(argv)

    reservations = read_config_file().get("reservations", [])
    valid_names = [item["name"] for item in reservations]

    if args.names:
        # Handle multiple args as well as a single-arg comma-delimited list.
        names = args.names if len(args.names) > 1 else args.names[0].split(",")
        for name in names:
            if name not in valid_names:
                print("Unknown reservation name: {}!".format(name))
                print("\nValid reservation names are: {}".format(" ".join(valid_names)))
                return 1
        selected_reservations = [r for r in reservations if r["name"] in names]
    else:
        # If no reservation names are specified, handle all reservations.
        selected_reservations = reservations

    results = [reconcile_reservation(r, plan=args.plan) for r in selected_reservations]
    print_summary_table(results)
    return 1 if any(r["action"] == "error" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
