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

installer="https://github.com/bazelbuild/bazel/releases/download/${BAZEL_VERSION}/bazel-${BAZEL_VERSION}-installer-${PLATFORM}.sh"
destination="/home/ci/.bazel/${BAZEL_VERSION}"

mkdir -p /home/ci/bootstrap-bazel
cd /home/ci/bootstrap-bazel

curl -L -o install.sh "${installer}"
chmod 0755 ./install.sh
rm -fr "${destination}"
mkdir -p "${destination}"
./install.sh \
    --base="${destination}" \
    --bin="${destination}/binary" \
    --bazelrc="${destination}/binary/bazel-real.bazelrc"
ln -s "${destination}" /home/ci/.bazel/latest

chown -R ci /home/ci/.bazel
rm -rf /home/ci/bootstrap-bazel
