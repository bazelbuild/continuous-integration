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
import sys
import tempfile

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
        "source_image_family": "windows-2022", # vs build tools failed to install on windows-2022-core
        "setup_script": "setup-windows.ps1",
        "guest_os_features": ["VIRTIO_SCSI_MULTIQUEUE"],
    },
    "windows-playground": {
        "project": "di-cloud-exp",
        "zone": "us-central1-f",
        "network": "default",
        "source_image_project": "windows-cloud",
        "source_image_family": "windows-2022",
        "setup_script": "setup-windows.ps1",
        "guest_os_features": ["VIRTIO_SCSI_MULTIQUEUE"],
    },
}


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
                f.write('Start-Process -FilePath "powershell.exe" -ArgumentList "-File c:\\setup.ps1" -RedirectStandardOutput "c:\\setup-stdout.log" -RedirectStandardError "c:\\setup-stderr.log" -NoNewWindow\n')
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


def workflow(name, params):
    instance_name = "%s-image-%s" % (name, int(datetime.now().timestamp()))
    project = params["project"]
    zone = params["zone"]
    try:
        # Create the VM.
        create_instance(instance_name, params)

        # Wait for the VM to become ready.
        gcloud_utils.wait_for_instance(instance_name, project=project, zone=zone, status="RUNNING")

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

    if len(argv) > 1:
        print("Only one platform can be created at a time.")
        return 1

    workflow(argv[0], IMAGE_CREATION_VMS[argv[0]])

    return 0


if __name__ == "__main__":
    sys.exit(main())
