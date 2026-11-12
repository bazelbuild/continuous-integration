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

"""Rolls back GCE VM image families to their previous image.

For each family, deprecates the newest active image with the previous one as
its replacement, so new VMs boot the previous image. Nothing is deleted, and
the undo command is printed.

Used by pipelines/vm-image-rollback.yml when image presubmits fail, and can be
run manually, e.g. if a problem shows up after promotion to prod:

  ./rollback_vm_image.py bk-docker,bk-docker-arm64
  ./create_instances.py bk-docker,bk-docker-arm64,bk-trusted-docker,bk-trusted-docker-arm64

Running it again rolls back one more image.
"""

import argparse
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys

import yaml

import gcloud

PROJECT = "bazel-public"


def load_family_groups():
    """Returns {image_family: [group_name, ...]} from instances.yml."""
    config = yaml.safe_load(Path(__file__).with_name("instances.yml").read_text(encoding="utf-8"))
    groups = {}
    for group in config["instance_groups"]:
        groups.setdefault(group["image_family"], []).append(group["name"])
    return groups


def select_rollback_images(family, images):
    """Returns (newest, previous) image names to roll back in the given family.

    Only images that are READY and not deprecated are considered, sorted by creation time.
    Raises RuntimeError if there are fewer than 2, since there is nothing to roll back to.
    """
    active = [
        img
        for img in images
        if img.get("family") == family
        and img.get("status") == "READY"
        and (img.get("deprecated") or {}).get("state", "ACTIVE") == "ACTIVE"
    ]
    active.sort(
        key=lambda img: datetime.fromisoformat(img["creationTimestamp"].replace("Z", "+00:00")),
        reverse=True,
    )
    if len(active) < 2:
        raise RuntimeError(f"Need at least 2 active images in {family}, found {len(active)}")
    return active[0]["name"], active[1]["name"]


def list_images(family):
    """Returns all images in the given family in bazel-public, including deprecated ones."""
    out = gcloud.gcloud(
        "compute", "images", "list", "--no-standard-images", "--show-deprecated", "--format=json",
        project=PROJECT, filter=f"family ~ ^{family}$",
    ).stdout
    return json.loads(out)


def error_text(ex):
    if isinstance(ex, subprocess.CalledProcessError) and ex.stderr:
        return ex.stderr.strip() or str(ex)
    return str(ex)


def print_deprecate_error(family, err):
    print(
        f"Rollback FAILED for {family}: {err}\n"
        "Families listed above as 'deprecated' were rolled back, but instances were "
        "NOT recreated. Use their Undo commands, or run create_instances.py for them.",
        file=sys.stderr,
    )


def main(argv=None):
    family_groups = load_family_groups()

    # Parse the command-line argument.
    parser = argparse.ArgumentParser(description="Roll back VM image families in bazel-public.")
    parser.add_argument(
        "families",
        help=f"Comma-separated image families: {', '.join(family_groups)}",
    )
    args = parser.parse_args(argv)

    # Split the comma-separated families into a de-duplicated list.
    families = list(dict.fromkeys(f.strip() for f in args.families.split(",") if f.strip()))
    if not families:
        parser.print_usage(sys.stderr)
        return 1

    # Reject unknown families before deprecating any image or looking up instance groups.
    unknown = [f for f in families if f not in family_groups]
    if unknown:
        print(
            f"Unknown families: {', '.join(unknown)}\n"
            f"Available families: {', '.join(family_groups)}",
            file=sys.stderr,
        )
        return 1

    # Look up the newest and previous image of every family before changing anything,
    # so we fail early if any family has nothing to roll back to.
    plan = []
    try:
        for family in families:
            newest, previous = select_rollback_images(family, list_images(family))
            plan.append((family, newest, previous))
    except (subprocess.CalledProcessError, RuntimeError) as ex:
        print(f"Rollback FAILED before any change: {error_text(ex)}. Nothing was changed.", file=sys.stderr)
        return 1
    except Exception as ex:
        print(f"Rollback FAILED before any change: {ex}. Nothing was changed.", file=sys.stderr)
        return 1

    # Deprecate the newest image in favor of the previous one and print the undo commands.
    for family, newest, previous in plan:
        try:
            gcloud.gcloud(
                "compute", "images", "deprecate", newest,
                state="DEPRECATED", replacement=previous, project=PROJECT,
            )
        except subprocess.CalledProcessError as ex:
            print_deprecate_error(family, error_text(ex))
            return 1
        except Exception as ex:
            print_deprecate_error(family, str(ex))
            return 1
        print(f"{family}: deprecated {newest} (replacement: {previous})")
        print(f"  Undo: gcloud compute images deprecate {newest} --state=ACTIVE --project={PROJECT}")
        print(f"        ./create_instances.py {','.join(family_groups[family])}")

    # Print create_instances.py for manual runs (the pipeline passes groups separately).
    groups = list(dict.fromkeys(g for f in families for g in family_groups[f]))
    print(f"\nNext step:\n  ./create_instances.py {','.join(groups)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
