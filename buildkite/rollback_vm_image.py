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


FAMILY_GROUPS = load_family_groups()


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


def main(argv=None):
    # Parse the command-line argument.
    parser = argparse.ArgumentParser(description="Roll back VM image families in bazel-public.")
    parser.add_argument(
        "families",
        help=f"Comma-separated image families: {', '.join(FAMILY_GROUPS)}",
    )
    args = parser.parse_args(argv)

    # Split the comma-separated families into a de-duplicated list.
    families = list(dict.fromkeys(f.strip() for f in args.families.split(",") if f.strip()))
    if not families:
        parser.print_usage(sys.stderr)
        return 1

    # Reject unknown families before deprecating any image or looking up instance groups.
    unknown = [f for f in families if f not in FAMILY_GROUPS]
    if unknown:
        print(
            f"Unknown families: {', '.join(unknown)}\n"
            f"Available families: {', '.join(FAMILY_GROUPS)}",
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
    except Exception as ex:
        err = (getattr(ex, "stderr", None) or "").strip() or str(ex)
        print(f"Rollback FAILED before any change: {err}. Nothing was changed.", file=sys.stderr)
        return 1

    # Deprecate the newest image in favor of the previous one and print the undo commands.
    rolled_back = []
    for i, (family, newest, previous) in enumerate(plan):
        try:
            gcloud.gcloud(
                "compute", "images", "deprecate", newest,
                state="DEPRECATED", replacement=previous, project=PROJECT,
            )
        except Exception as ex:
            err = (getattr(ex, "stderr", None) or "").strip() or str(ex)
            done = ", ".join(f"{f} ({n} -> {p})" for f, n, p in rolled_back) or "(none)"
            remaining = ", ".join(f for f, _, _ in plan[i + 1 :]) or "(none)"
            print(f"Rollback FAILED for {family}:", file=sys.stderr)
            print(f"  Rolled back:   {done}", file=sys.stderr)
            print(f"  Failed:        {family}: {err}", file=sys.stderr)
            print(f"  Not attempted: {remaining}", file=sys.stderr)
            rb_groups = ",".join(
                dict.fromkeys(g for f, _, _ in rolled_back for g in FAMILY_GROUPS[f])
            )
            finish = f" To finish: ./create_instances.py {rb_groups}" if rb_groups else ""
            print(f"Instances were NOT recreated.{finish}", file=sys.stderr)
            for f, n, _ in rolled_back:
                cmd = f"gcloud compute images deprecate {n} --state=ACTIVE --project={PROJECT}"
                print(f"To undo {f}: {cmd}", file=sys.stderr)
            return 1
        rolled_back.append((family, newest, previous))
        family_groups = ",".join(FAMILY_GROUPS[family])
        print(f"{family}: deprecated {newest} (replacement: {previous})")
        print(
            f"  Undo: gcloud compute images deprecate {newest} --state=ACTIVE --project={PROJECT}"
        )
        print(f"        ./create_instances.py {family_groups}")

    # Print create_instances.py for manual runs (the pipeline passes groups separately).
    groups = list(dict.fromkeys(g for f in families for g in FAMILY_GROUPS[f]))
    print(f"\nNext step:\n  ./create_instances.py {','.join(groups)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
