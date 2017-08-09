# Copyright 2016 The Bazel Authors. All rights reserved.
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


# Install a bootstrap bazel; we use the latest released version
PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m)
BAZEL_VERSION=$(curl -I https://github.com/bazelbuild/bazel/releases/latest | grep '^Location: ' | sed 's|.*/||' | sed $'s/\r//')

CI_HOME="$(echo ~ci)"

mkdir -p "${CI_HOME}/bootstrap-bazel"
cd "${CI_HOME}/bootstrap-bazel"

installer="https://releases.bazel.build/${BAZEL_VERSION}/release/bazel-${BAZEL_VERSION}-without-jdk-installer-${PLATFORM}.sh"
destination="${CI_HOME}/.bazel/${BAZEL_VERSION}"
curl -L -o install.sh "${installer}"
chmod 0755 ./install.sh
rm -fr "${destination}"
mkdir -p "${destination}"
./install.sh \
    --base="${destination}" \
    --bin="${destination}/binary"
ln -s "${destination}" "${CI_HOME}/.bazel/latest"

chown -R ci "${CI_HOME}/.bazel"
rm -rf "${CI_HOME}/bootstrap-bazel"
