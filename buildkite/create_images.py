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
from typing import Any, Dict, List, Optional

import gcloud
import gcloud_utils

DEBUG: bool = False
DEFAULT_MACHINE_TYPE: str = "c2-standard-8"
DEFAULT_BOOT_DISK_TYPE: str = "pd-ssd"

IMAGE_CREATION_VMS: Dict[str, Dict[str, Any]] = {
    "bk-testing-docker": {
        "project": "bazel-public",
        "zone": "us-central1-f",
        "source_image_project": "ubuntu-os-cloud",
        "source_image_family": "ubuntu-2204-lts",
        "setup_script": "setup-docker.sh",
        "guest_os_features": ["VIRTIO_SCSI_MULTIQUEUE"],
        "licenses": [
            "https://www.googleapis.com/compute/v1/projects/vm-options/global/licenses/enable-vmx"
        ],
    },
    "bk-testing-docker-arm64": {
        "project": "bazel-public",
        "zone": "us-central1-c",
        "source_image_project": "ubuntu-os-cloud",
        "source_image_family": "ubuntu-2204-lts-arm64",
        "setup_script": "setup-docker.sh",
        "guest_os_features": ["VIRTIO_SCSI_MULTIQUEUE"],
        "licenses": [
            "https://www.googleapis.com/compute/v1/projects/vm-options/global/licenses/enable-vmx"
        ],
        "machine_type": "c4a-standard-8-lssd",
        "boot_disk_type": "hyperdisk-balanced",
    },
    "bk-testing-windows": {
        "project": "bazel-public",
        "zone": "us-central1-f",
        "source_image_project": "windows-cloud",
        "source_image_family": "windows-2022",  # vs build tools failed to install on windows-2022-core
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


def preprocess_setup_script(setup_script: str, is_windows: bool) -> str:
    fd, output_file = tempfile.mkstemp()
    os.close(fd)
    newline = "\r\n" if is_windows else "\n"
    with open(output_file, "w", newline=newline) as f:
        with open(setup_script, "r") as setup_script_file:
            if is_windows:
                f.write("$setup_script = @'\n")
            f.write(setup_script_file.read() + "\n")
            if is_windows:
                f.write("'@\n")
                f.write('[System.IO.File]::WriteAllLines("c:\\setup.ps1", $setup_script)\n')
                f.write("$ts = Get-Date -Format 'yyyyMMdd-HHmmss'\n")
                f.write(
                    'Start-Process -FilePath "powershell.exe" -ArgumentList "-File c:\\setup.ps1" -RedirectStandardOutput "c:\\setup-stdout-$ts.log" -RedirectStandardError "c:\\setup-stderr-$ts.log" -NoNewWindow\n'
                )
    return output_file


def create_instance(instance_name: str, params: Dict[str, Any]) -> None:
    is_windows = "windows" in instance_name
    setup_script = preprocess_setup_script(params["setup_script"], is_windows)
    try:
        if is_windows:
            startup_script = "windows-startup-script-ps1=" + setup_script
        else:
            startup_script = "startup-script=" + setup_script

        image_kwargs: Dict[str, str] = {}
        if "source_image" in params:
            image_kwargs["image"] = params["source_image"]
        else:
            image_kwargs["image-project"] = params["source_image_project"]
            image_kwargs["image-family"] = params["source_image_family"]

        gcloud.create_instance(
            instance_name,
            project=params["project"],
            zone=params["zone"],
            machine_type=params.get("machine_type", DEFAULT_MACHINE_TYPE),
            network=params.get("network", "default"),
            metadata_from_file=startup_script,
            boot_disk_type=params.get("boot_disk_type", DEFAULT_BOOT_DISK_TYPE),
            boot_disk_size=params.get("boot_disk_size", "500GB"),
            **image_kwargs,
        )
    finally:
        os.remove(setup_script)


def workflow(name: str, params: Dict[str, Any]) -> None:
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


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("Usage: create_images.py {}".format(" ".join(IMAGE_CREATION_VMS.keys())))
        return 1

    # Handle multiple args as well as a single-arg comma-delimited list.
    names = argv if len(argv) > 1 else argv[0].split(",")

    unknown_args = set(names).difference(IMAGE_CREATION_VMS.keys())
    if unknown_args:
        print(
            "Unknown platforms: {}\nAvailable platforms: {}".format(
                ", ".join(unknown_args), ", ".join(IMAGE_CREATION_VMS.keys())
            )
        )
        return 1

    for n in names:
        workflow(n, IMAGE_CREATION_VMS[n])

    return 0


if __name__ == "__main__":
    sys.exit(main())
