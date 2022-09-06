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
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading

import gcloud
import gcloud_utils

DEBUG = False

IMAGE_CREATION_VMS = {
    "bk-testing-docker": {
        "project": "bazel-public",
        "zone": "us-central1-f",
        "source_image_project": "ubuntu-os-cloud",
        "source_image_family": "ubuntu-2004-lts",
        "setup_script": "setup-docker.sh",
        "guest_os_features": ["VIRTIO_SCSI_MULTIQUEUE"],
        "licenses": [
            "https://www.googleapis.com/compute/v1/projects/vm-options/global/licenses/enable-vmx"
        ],
    },
    "bk-testing-windows": {
        "project": "bazel-public",
        "zone": "us-central1-f",
        "source_image_project": "windows-cloud",
        "source_image_family": "windows-2019-core",
        "setup_script": "setup-windows.ps1",
        "guest_os_features": ["VIRTIO_SCSI_MULTIQUEUE"],
    },
    "windows-playground": {
        "project": "di-cloud-exp",
        "zone": "us-central1-f",
        "network": "default",
        "source_image_project": "windows-cloud",
        "source_image_family": "windows-2019",
        "setup_script": "setup-windows.ps1",
        "guest_os_features": ["VIRTIO_SCSI_MULTIQUEUE"],
    },
}

WORK_QUEUE = queue.Queue()


def run(args, **kwargs):
    return subprocess.run(args, **kwargs)


def preprocess_setup_script(setup_script, is_windows):
    output_file = tempfile.mkstemp()[1]
    newline = "\r\n" if is_windows else "\n"
    with open(output_file, "w", newline=newline) as f:
        with open(setup_script, "r") as setup_script_file:
            if is_windows:
                f.write("$setup_script = @'\n")
            f.write(setup_script_file.read() + "\n")
            if is_windows:
                f.write("'@\n")
                f.write('[System.IO.File]::WriteAllLines("c:\\setup.ps1", $setup_script)\n')
    return output_file


def create_instance(instance_name, params):
    is_windows = "windows" in instance_name
    setup_script = preprocess_setup_script(params["setup_script"], is_windows)
    try:
        if is_windows:
            startup_script = "windows-startup-script-ps1=" + setup_script
        else:
            startup_script = "startup-script=" + setup_script

        if "source_image" in params:
            image = {"image": params["source_image"]}
        else:
            image = {
                "image-project": params["source_image_project"],
                "image-family": params["source_image_family"],
            }

        gcloud.create_instance(
            instance_name,
            project=params["project"],
            zone=params["zone"],
            machine_type="c2-standard-8",
            network=params.get("network", "default"),
            metadata_from_file=startup_script,
            boot_disk_type="pd-ssd",
            boot_disk_size=params.get("boot_disk_size", "500GB"),
            **image,
        )
    finally:
        os.remove(setup_script)


# https://stackoverflow.com/a/25802742
def write_to_clipboard(output):
    process = subprocess.Popen("pbcopy", env={"LANG": "en_US.UTF-8"}, stdin=subprocess.PIPE)
    process.communicate(output.encode("utf-8"))


def print_windows_instructions(project, zone, instance_name):
    tail_start = gcloud_utils.tail_serial_console(
        instance_name, project=project, zone=zone, until="Finished running startup scripts"
    )

    pw = json.loads(
        gcloud.reset_windows_password(
            instance_name, format="json", project=project, zone=zone
        ).stdout
    )
    rdp_file = tempfile.mkstemp(suffix=".rdp")[1]
    with open(rdp_file, "w") as f:
        f.write("full address:s:" + pw["ip_address"] + "\n")
        f.write("username:s:" + pw["username"] + "\n")
    subprocess.run(["open", rdp_file])
    write_to_clipboard(pw["password"])
    with gcloud.PRINT_LOCK:
        print("Use this password to connect to the Windows VM: " + pw["password"])
        print("Please run the setup script C:\\setup.ps1 once you're logged in.")

    # Wait until the VM reboots once, then open RDP again.
    tail_start = gcloud_utils.tail_serial_console(
        instance_name,
        project=project,
        zone=zone,
        start=tail_start,
        until="GCEGuestAgent: GCE Agent Started",
    )
    print("Connecting via RDP a second time to finish the setup...")
    write_to_clipboard(pw["password"])
    run(["open", rdp_file])
    return tail_start


def workflow(name, params):
    instance_name = "%s-image-%s" % (name, int(datetime.now().timestamp()))
    project = params["project"]
    zone = params["zone"]
    try:
        # Create the VM.
        create_instance(instance_name, params)

        # Wait for the VM to become ready.
        gcloud_utils.wait_for_instance(instance_name, project=project, zone=zone, status="RUNNING")

        if "windows" in instance_name:
            # Wait for VM to be ready, then print setup instructions.
            tail_start = print_windows_instructions(project, zone, instance_name)
            # Continue printing the serial console until the VM shuts down.
            gcloud_utils.tail_serial_console(
                instance_name, project=project, zone=zone, start=tail_start
            )
        else:
            # Continuously print the serial console.
            gcloud_utils.tail_serial_console(instance_name, project=project, zone=zone)

        # Wait for the VM to completely shutdown.
        gcloud_utils.wait_for_instance(
            instance_name, project=project, zone=zone, status="TERMINATED"
        )

        # Create a new image from our VM.
        gcloud.create_image(
            instance_name,
            project=project,
            family=name,
            source_disk=instance_name,
            source_disk_zone=zone,
            licenses=params.get("licenses", []),
            guest_os_features=params.get("guest_os_features", []),
        )
    finally:
        gcloud.delete_instance(instance_name, project=project, zone=zone)


def worker():
    while True:
        item = WORK_QUEUE.get()
        if not item:
            break
        try:
            workflow(**item)
        finally:
            WORK_QUEUE.task_done()


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("Usage: create_images.py {}".format(" ".join(IMAGE_CREATION_VMS.keys())))
        return 1

    unknown_args = set(argv).difference(IMAGE_CREATION_VMS.keys())
    if unknown_args:
        print(
            "Unknown platforms: {}\nAvailable platforms: {}".format(
                ", ".join(unknown_args), ", ".join(IMAGE_CREATION_VMS.keys())
            )
        )
        return 1

    # Put VM creation instructions into the work queue.
    for name in argv:
        WORK_QUEUE.put({"name": name, "params": IMAGE_CREATION_VMS[name]})

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
