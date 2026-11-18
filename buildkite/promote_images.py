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

import os
import queue
import shutil
import subprocess
import sys
import threading

import gcloud

DEBUG = False

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


def workflow(name, params):
    source_image_name = get_recorded_image(params["source_image_family"])
    if source_image_name:
        source_kwargs = {"source_image": source_image_name}
    else:
        # Fall back to the current image in the source family (e.g. local runs).
        source_image_name = gcloud.describe_image_family(
            params["source_image_family"], project=params["source_image_project"]
        )["name"]
        source_kwargs = {"source_image_family": params["source_image_family"]}

    # Promote the testing image to the production image.
    gcloud.create_image(
        source_image_name.replace("-testing", ""),
        project=params["project"],
        family=name,
        guest_os_features=params.get("guest_os_features", []),
        licenses=params.get("licenses", []),
        source_image_project=params["source_image_project"],
        **source_kwargs,
    )


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
