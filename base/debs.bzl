# Copyright 2015 The Bazel Authors. All rights reserved.
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

# Generate debs list for specific image from the generated file
load(":generated.bzl", "DEBS")

def deb_repo_name(distrib, package):
  return "deb_%s_%s" % (distrib.replace("-", "_"), package.replace("+", "p").replace("-", "_").replace(".", "_"))

DEB_NAMES = {
    k: ["@%s//file" % deb_repo_name(k, deb[0]) for deb in DEBS[k]]
    for k in DEBS
    }

DEB_URL="http://se.archive.ubuntu.com/ubuntu/%s"

def docker_debs_repositories():
  [[native.http_file(
      name = deb_repo_name(k, deb[0]),
      sha256 = deb[2],
      url = DEB_URL % deb[1],
      ) for deb in DEBS[k]]
   for k in DEBS]
