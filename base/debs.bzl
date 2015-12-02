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
load("generated", "DEBS")

DEB_NAMES = {
    k: ["@deb-%s-%s//file" % (k, deb[0].replace("+", "p")) for deb in DEBS[k]]
    for k in DEBS
    }

DEB_URL="http://se.archive.ubuntu.com/ubuntu/%s"

def docker_debs_repositories():
  [[native.http_file(
      name = "deb-%s-%s" % (k, deb[0].replace("+", "p")),
      sha256 = deb[2],
      url = DEB_URL % deb[1],
      ) for deb in DEBS[k]]
   for k in DEBS]
