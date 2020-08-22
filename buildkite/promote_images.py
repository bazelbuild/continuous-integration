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

import queue
import sys
import threading

import gcloud

DEBUG = False

IMAGE_PROMOTIONS = {
    "bk-docker": {
        "project": "bazel-public",
        "source_image_project": "bazel-public",
        "source_image_family": "bk-testing-docker",
        "guest_os_features": ["VIRTIO_SCSI_MULTIQUEUE"],
    },
    "bk-windows": {
        "project": "bazel-public",
        "source_image_project": "bazel-public",
        "source_image_family": "bk-testing-windows",
        "guest_os_features": ["VIRTIO_SCSI_MULTIQUEUE"],
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


def workflow(name, params):
    # Get the name from the current image in the source family.
    source_image = gcloud.describe_image_family(
        params["source_image_family"], project=params["source_image_project"]
    )

    # Promote the testing image to the production image.
    gcloud.create_image(
        source_image["name"].replace("-testing", ""),
        project=params["project"],
        family=name,
        guest_os_features=params.get("guest_os_features", []),
        licenses=params.get("licenses", []),
        source_image_family=params["source_image_family"],
        source_image_project=params["source_image_project"],
    )


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("Usage: promote_images.py {}".format(" ".join(IMAGE_PROMOTIONS.keys())))
        return 1

    unknown_args = set(argv).difference(IMAGE_PROMOTIONS.keys())
    if unknown_args:
        print(
            "Unknown platforms: {}\nAvailable platforms: {}".format(
                ", ".join(unknown_args), ", ".join(IMAGE_PROMOTIONS.keys())
            )
        )
        return 1

    # Put VM creation instructions into the work queue.
    for name in argv:
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
