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
import shlex
import sys
import yaml

import gcloud


def format_gcloud_command(*args, **kwargs):
    cmd = ["gcloud"] + list(args)
    for flag, value in kwargs.items():
        flag = flag.replace("_", "-")
        if isinstance(value, bool):
            cmd += ["--" + ("no-" if not value else "") + flag]
        elif gcloud.is_sequence(value):
            for item in value:
                cmd += ["--" + flag, str(item)]
        else:
            cmd += ["--" + flag, str(value)]
    return " ".join(shlex.quote(part) for part in cmd)


def reconcile_reservation(config, dry_run=False):
    reservation_name = config.pop("name")
    project = config.pop("project", None)
    zone = config.pop("zone", None)
    config.pop("region", None)
    machine_type = config.pop("machine_type", None)
    count = config.pop("count", None)
    description = config.pop("description", None)
    description_prefix = config.pop("description_prefix", None)

    summary = {
        "name": reservation_name,
        "project": project or "-",
        "zone": zone or "-",
        "machine_type": machine_type or "-",
        "current_count": "-",
        "desired_count": str(count) if count is not None else "-",
        "action": "error",
        "returncode": 1,
    }

    try:
        if not project:
            raise Exception("Invalid reservation config, no project name set")
        if not zone:
            raise Exception("Invalid reservation config, no zone set")
        if not machine_type:
            raise Exception("Invalid reservation config, no machine_type set")
        if count is None or int(count) <= 0:
            raise Exception("Invalid reservation config, count must be a positive integer")

        count = int(count)
        summary["desired_count"] = str(count)

        if description_prefix and description:
            if description.startswith(description_prefix):
                full_description = description
            else:
                full_description = f"{description_prefix}: {description}"
        elif description:
            full_description = description
        elif description_prefix:
            full_description = f"{description_prefix} ({reservation_name})"
        else:
            full_description = None

        existing = gcloud.describe_reservation(reservation_name, project=project, zone=zone)

        if existing is None:
            create_kwargs = {
                "project": project,
                "zone": zone,
                "machine_type": machine_type,
                "vm_count": count,
            }
            if full_description:
                create_kwargs["description"] = full_description
            create_kwargs.update(config)

            if dry_run:
                cmd_str = format_gcloud_command(
                    "compute", "reservations", "create", reservation_name, **create_kwargs
                )
                print(f"[DRY RUN] {cmd_str}")
                summary["action"] = "create (dry-run)"
            else:
                gcloud.create_reservation(reservation_name, **create_kwargs)
                print(
                    f"Created reservation {reservation_name} "
                    f"({count}x {machine_type} in {project}/{zone})"
                )
                summary["action"] = "created"
            summary["returncode"] = 0
            return summary

        spec = existing.get("specificReservation", {})
        props = spec.get("instanceProperties", {})
        existing_machine_type = props.get("machineType", "").split("/")[-1]
        existing_count = int(spec.get("count", 0))
        summary["current_count"] = str(existing_count)

        if existing_machine_type != machine_type:
            raise Exception(
                f"Reservation {reservation_name} in {project}/{zone} has machine_type "
                f"'{existing_machine_type}', but config specifies '{machine_type}'. "
                f"GCE cannot change a reservation's machine type in place; "
                f"delete and recreate it manually."
            )

        if existing_count != count:
            update_kwargs = {
                "project": project,
                "zone": zone,
                "vm_count": count,
            }
            if dry_run:
                cmd_str = format_gcloud_command(
                    "compute", "reservations", "update", reservation_name, **update_kwargs
                )
                print(f"[DRY RUN] {cmd_str}")
                summary["action"] = f"update {existing_count} -> {count} (dry-run)"
            else:
                gcloud.update_reservation(reservation_name, **update_kwargs)
                print(
                    f"Updated reservation {reservation_name} in {project}/{zone}: "
                    f"vm-count {existing_count} -> {count}"
                )
                summary["action"] = f"updated ({existing_count} -> {count})"
            summary["returncode"] = 0
            return summary

        print(
            f"Reservation {reservation_name} already matches config "
            f"({count}x {machine_type} in {project}/{zone}): no-op"
        )
        summary["action"] = "no-op"
        summary["returncode"] = 0
        return summary
    except Exception as ex:
        print(f"Failed to reconcile reservation {reservation_name}: {ex}", file=sys.stderr)
        return summary


def print_summary_table(results):
    headers = ("NAME", "PROJECT", "ZONE", "MACHINE_TYPE", "CURRENT", "DESIRED", "ACTION")
    rows = [
        (
            r["name"],
            r["project"],
            r["zone"],
            r["machine_type"],
            r["current_count"],
            r["desired_count"],
            r["action"],
        )
        for r in results
    ]
    widths = [
        max(len(headers[i]), *(len(row[i]) for row in rows)) if rows else len(headers[i])
        for i in range(len(headers))
    ]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print("\n" + fmt.format(*headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(fmt.format(*row))


def read_config_file():
    path = os.path.join(os.getcwd(), "reservations.yml")
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reservations.yml")
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
        "--all",
        action="store_true",
        help="Reconcile all reservations in reservations.yml (default when no names are given).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check existing reservations and print planned gcloud create/update commands without mutating anything.",
    )

    args = parser.parse_args(argv)

    config = read_config_file()
    reservations = config.get("reservations", [])
    default_reservation = config.get("default_reservation", {})
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
        selected_reservations = reservations

    results = [
        reconcile_reservation({**default_reservation, **r}, dry_run=args.dry_run)
        for r in selected_reservations
    ]
    print_summary_table(results)
    return max((r["returncode"] for r in results), default=0)


if __name__ == "__main__":
    sys.exit(main())
