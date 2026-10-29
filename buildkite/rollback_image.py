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

from datetime import datetime
import json
import sys

import gcloud

PROJECT = "bazel-public"
FAMILY_GROUPS = {
    "bk-testing-docker": ("bk-testing-docker",),
    "bk-testing-docker-arm64": ("bk-testing-docker-arm64",),
    "bk-testing-windows": ("bk-testing-windows",),
    "bk-docker": ("bk-docker", "bk-trusted-docker"),
    "bk-docker-arm64": ("bk-docker-arm64", "bk-trusted-docker-arm64"),
    "bk-windows": ("bk-windows", "bk-trusted-windows"),
}


def select_rollback_images(family, images):
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
    out = gcloud.gcloud(
        "compute", "images", "list", "--no-standard-images", "--show-deprecated", "--format=json",
        project=PROJECT, filter=f"family ~ ^{family}$",
    ).stdout
    return json.loads(out)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    families = list(dict.fromkeys(f.strip() for arg in argv for f in arg.split(",") if f.strip()))
    if not families:
        print(f"Usage: rollback_image.py <family>[,<family>...] ({', '.join(FAMILY_GROUPS)})")
        return 1

    unknown = [f for f in families if f not in FAMILY_GROUPS]
    if unknown:
        print(
            f"Unknown families: {', '.join(unknown)}\n"
            f"Available families: {', '.join(FAMILY_GROUPS)}",
            file=sys.stderr,
        )
        return 1

    plan = [(f, *select_rollback_images(f, list_images(f))) for f in families]
    for family, newest, previous in plan:
        gcloud.gcloud(
            "compute", "images", "deprecate", newest,
            state="DEPRECATED", replacement=previous, project=PROJECT,
        )
        print(f"{family}: deprecated {newest} (replacement: {previous})")
        print(
            f"  Undo: gcloud compute images deprecate {newest} --state=ACTIVE --project={PROJECT}"
        )

    groups = list(dict.fromkeys(g for f in families for g in FAMILY_GROUPS[f]))
    print(f"\nNext step:\n  ./create_instances.py {','.join(groups)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
