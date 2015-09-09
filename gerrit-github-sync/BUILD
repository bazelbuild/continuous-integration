# Copyright 2015 Google Inc. All rights reserved.
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

# A slave for polling and syncing gerrit and github
load("/tools/build_defs/docker/docker", "docker_build")

docker_build(
    name = "ubuntu-utopic-amd64-ssh",
    base = "//jenkins:ubuntu-utopic-amd64",
    debs = [
        "@deb-ubuntu-utopic-amd64-ssh-adduser//file",
        "@deb-ubuntu-utopic-amd64-ssh-cdebconf//file",
        "@deb-ubuntu-utopic-amd64-ssh-debianutils//file",
        "@deb-ubuntu-utopic-amd64-ssh-init-system-helpers//file",
        "@deb-ubuntu-utopic-amd64-ssh-initscripts//file",
        "@deb-ubuntu-utopic-amd64-ssh-insserv//file",
        "@deb-ubuntu-utopic-amd64-ssh-libaudit-common//file",
        "@deb-ubuntu-utopic-amd64-ssh-libaudit1//file",
        "@deb-ubuntu-utopic-amd64-ssh-libblkid1//file",
        "@deb-ubuntu-utopic-amd64-ssh-libck-connector0//file",
        "@deb-ubuntu-utopic-amd64-ssh-libcomerr2//file",
        "@deb-ubuntu-utopic-amd64-ssh-libdebian-installer4//file",
        "@deb-ubuntu-utopic-amd64-ssh-libmount1//file",
        "@deb-ubuntu-utopic-amd64-ssh-libncurses5//file",
        "@deb-ubuntu-utopic-amd64-ssh-libpam-modules//file",
        "@deb-ubuntu-utopic-amd64-ssh-libpam-modules-bin//file",
        "@deb-ubuntu-utopic-amd64-ssh-libpam-runtime//file",
        "@deb-ubuntu-utopic-amd64-ssh-libpam0g//file",
        "@deb-ubuntu-utopic-amd64-ssh-libprocps3//file",
        "@deb-ubuntu-utopic-amd64-ssh-libsemanage-common//file",
        "@deb-ubuntu-utopic-amd64-ssh-libsemanage1//file",
        "@deb-ubuntu-utopic-amd64-ssh-libsepol1//file",
        "@deb-ubuntu-utopic-amd64-ssh-libslang2//file",
        "@deb-ubuntu-utopic-amd64-ssh-libsmartcols1//file",
        "@deb-ubuntu-utopic-amd64-ssh-libtextwrap1//file",
        "@deb-ubuntu-utopic-amd64-ssh-mount//file",
        "@deb-ubuntu-utopic-amd64-ssh-openssh-client//file",
        "@deb-ubuntu-utopic-amd64-ssh-openssh-server//file",
        "@deb-ubuntu-utopic-amd64-ssh-openssh-sftp-server//file",
        "@deb-ubuntu-utopic-amd64-ssh-passwd//file",
        "@deb-ubuntu-utopic-amd64-ssh-procps//file",
        "@deb-ubuntu-utopic-amd64-ssh-sensible-utils//file",
        "@deb-ubuntu-utopic-amd64-ssh-ssh//file",
        "@deb-ubuntu-utopic-amd64-ssh-sysv-rc//file",
        "@deb-ubuntu-utopic-amd64-ssh-sysvinit-utils//file",
    ],
)

docker_build(
    name = "gerrit-github-sync",
    base = ":ubuntu-utopic-amd64-ssh",
    files = ["gerrit-github-sync.sh"],
    entrypoint = [
        "/bin/bash",
        "/gerrit-github-sync.sh",
    ],
    volumes = ["/opt/secrets"],
)
