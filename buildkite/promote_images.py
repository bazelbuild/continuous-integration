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

from datetime import datetime
import os
import queue
import shutil
import subprocess
import sys
import threading

import gcloud

DEBUG = False
KEEP_IMAGES_PER_FAMILY = 2

IMAGE_PROMOTIONS = {
    "bk-docker": {
        "project": "bazel-public",
        "source_image_project": "bazel-public",
        "source_image_family": "bk-testing-docker",
        "guest_os_features": ["VIRTIO_SCSI_MULTIQUEUE", "GVNIC"],
        "licenses": [
            "https://www.googleapis.com/compute/v1/projects/vm-options/global/licenses/enable-vmx"
        ],
    },
    "bk-docker-arm64": {
        "project": "bazel-public",
        "source_image_project": "bazel-public",
        "source_image_family": "bk-testing-docker-arm64",
        "guest_os_features": ["VIRTIO_SCSI_MULTIQUEUE", "GVNIC"],
        "licenses": [
            "https://www.googleapis.com/compute/v1/projects/vm-options/global/licenses/enable-vmx"
        ],
    },
    "bk-windows": {
        "project": "bazel-public",
        "source_image_project": "bazel-public",
        "source_image_family": "bk-testing-windows",
        "guest_os_features": ["VIRTIO_SCSI_MULTIQUEUE", "GVNIC"],
    },
}

WORK_QUEUE = queue.Queue()


def worker():
    while True:
        item = WORK_QUEUE.get()
        if not item:
            break
        try:
            workflow(**item)
        finally:
            WORK_QUEUE.task_done()


def get_recorded_image(source_family):
    if not os.environ.get("BUILDKITE") or not shutil.which("buildkite-agent"):
        return None
    result = subprocess.run(
        ["buildkite-agent", "meta-data", "get", f"vm-image-{source_family}", "--default", ""],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def cleanup_old_images(project, family, keep_image, keep_count=KEEP_IMAGES_PER_FAMILY):
    try:
        images = [
            img
            for img in gcloud.list_images(
                project=project,
                standard_images=False,
                show_deprecated=True,
                filter=f"family ~ ^{family}$",
            )
            if img.get("family") == family
        ]
    except Exception as ex:
        with gcloud.PRINT_LOCK:
            print(
                f"Warning: failed to list images for family {family} in {project}: {ex}",
                file=sys.stderr,
            )
        return

    images.sort(
        key=lambda img: datetime.fromisoformat(img["creationTimestamp"].replace("Z", "+00:00")),
        reverse=True,
    )
    to_keep = {img["name"] for img in images[:keep_count]}
    if keep_image:
        to_keep.add(keep_image)

    for img in images:
        img_name = img["name"]
        if img_name in to_keep:
            continue
        with gcloud.PRINT_LOCK:
            print(f"Deleting old image {img_name} from family {family} (project {project})")
        try:
            gcloud.delete_image(img_name, project=project)
        except Exception as ex:
            with gcloud.PRINT_LOCK:
                print(
                    f"Warning: failed to delete old image {img_name} from {family}: {ex}",
                    file=sys.stderr,
                )


def workflow(name, params):
    source_family = params["source_image_family"]
    source_project = params["source_image_project"]
    source_image_name = get_recorded_image(source_family)
    if source_image_name:
        with gcloud.PRINT_LOCK:
            print(f"Promoting recorded image {source_image_name} from {source_family} to {name}")
        source_kwargs = {"source_image": source_image_name}
    else:
        # Fall back to the current image in the source family (e.g. local runs).
        source_image_name = gcloud.describe_image_family(
            source_family, project=source_project
        )["name"]
        with gcloud.PRINT_LOCK:
            print(
                f"Promoting latest image {source_image_name} from family {source_family} to {name} "
                "(no recorded build metadata)"
            )
        source_kwargs = {"source_image_family": source_family}

    target_image_name = source_image_name.replace("-testing", "")

    # Promote the testing image to the production image.
    gcloud.create_image(
        target_image_name,
        project=params["project"],
        family=name,
        guest_os_features=params.get("guest_os_features", []),
        licenses=params.get("licenses", []),
        source_image_project=source_project,
        **source_kwargs,
    )

    # Delete older images beyond the newest 2 in both the source and target families.
    cleanup_old_images(source_project, source_family, keep_image=source_image_name)
    cleanup_old_images(params["project"], name, keep_image=target_image_name)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("Usage: promote_images.py {}".format(" ".join(IMAGE_PROMOTIONS.keys())))
        return 1

    # Handle multiple args as well as a single-arg comma-delimited list.
    names = argv if len(argv) > 1 else argv[0].split(",")

    unknown_args = set(names).difference(IMAGE_PROMOTIONS.keys())
    if unknown_args:
        print(
            "Unknown platforms: {}\nAvailable platforms: {}".format(
                ", ".join(unknown_args), ", ".join(IMAGE_PROMOTIONS.keys())
            )
        )
        return 1

    # Put VM creation instructions into the work queue.
    for name in names:
        WORK_QUEUE.put({"name": name, "params": IMAGE_PROMOTIONS[name]})

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
