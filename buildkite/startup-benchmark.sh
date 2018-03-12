#!/bin/bash
#
# Copyright 2017 The Bazel Authors. All rights reserved.
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

set -euxo pipefail

# Give various other start-up scripts / daily tasks some time to finish.
sleep 30

# If available: Use the local SSD as swap space.
if [[ -e /dev/nvme0n1 ]]; then
  mkswap -f /dev/nvme0n1
  swapon /dev/nvme0n1
fi

# Move fast and lose data.
mount -t tmpfs -o mode=1777,uid=root,gid=root,size=$((100 * 1024 * 1024 * 1024)) tmpfs /tmp
mount -t tmpfs -o mode=0711,uid=root,gid=root,size=$((100 * 1024 * 1024 * 1024)) tmpfs /var/lib/docker
mount -t tmpfs -o mode=0755,uid=root,gid=root,size=$((100 * 1024 * 1024 * 1024)) tmpfs /root

set +x

# Download a snapshot of Bazel's source code. We don't clone from GitHub here, as we otherwise run
# into rate limiting.
cd /root
curl -s https://storage.googleapis.com/bazel-benchmark/bazel.tar.xz | tar xJ
cd bazel

# Install Maven, as otherwise Bazel's "fetch //..." complains about it not being found.
apt-get update && apt-get install -y maven

export ANDROID_HOME=/opt/android-sdk-linux
export ANDROID_NDK_HOME=/opt/android-ndk-r15c

sed -i \
  -e 's!^# android_sdk_repository!android_sdk_repository!' \
  -e 's!^# android_ndk_repository!android_ndk_repository!' \
  -e 's!^# load("//tools/build_defs/repo:maven_rules.bzl"!load("//tools/build_defs/repo:maven_rules.bzl"!' \
  -e 's!^# maven_dependency_plugin!maven_dependency_plugin!' \
  WORKSPACE

BUILD_TARGETS="//src:bazel"
TEST_TARGETS="//scripts/... //src/test/... //third_party/ijar/... //tools/android/..."
TEST_BLACKLIST="-//src/test/shell/bazel/android:android_ndk_integration_test \
  -//src/test/shell/integration:loading_phase_tests \
  -//src/test/java/com/google/devtools/build/lib:vfs_test \
  -//src/test/cpp/util:file_test \
  -//src/test/java/com/google/devtools/build/lib:unix_test \
  -//src/test/shell/bazel:bazel_sandboxing_test \
  -//src/test/shell/bazel:git_repository_test \
  -//src/test/shell/bazel:skylark_git_repository_test \
  -//scripts/release:relnotes_test \
  -//scripts/release:release_test"

echo "=== HARDWARE INFO START ==="
VCPUS=$(cat /proc/cpuinfo  | grep ^processor | wc -l)
echo "CPU_COUNT=${VCPUS}"
RAMSIZE=$(free -g | head -2 | tail -1 | awk '{print $2}')
echo "RAM_GB=${RAMSIZE}"
echo "CPU_PLATFORM=$(gcloud compute instances describe \
    --zone $(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/zone" -H Metadata-Flavor:Google) \
    $(hostname) | grep ^cpuPlatform | cut -d':' -f2 | sed -e 's/^[[:space:]]*//')"
echo "=== HARDWARE INFO DONE ==="

echo "=== BAZEL INFO START @$(date +'%s.%N') ==="
set -x
bazel info
set +x
echo "=== BAZEL INFO DONE @$(date +'%s.%N') ==="

echo "=== BAZEL FETCH START @$(date +'%s.%N') ==="
set -x
bazel fetch -- $BUILD_TARGETS $TEST_TARGETS
set +x
echo "=== BAZEL FETCH DONE @$(date +'%s.%N') ==="

echo "=== BAZEL BUILD START @$(date +'%s.%N') ==="
set -x
bazel build \
  --noexperimental_ui \
  --jobs=$VCPUS \
  --experimental_multi_threaded_digest \
  --sandbox_tmpfs_path=/tmp \
  -- \
  $BUILD_TARGETS
set +x
echo "=== BAZEL BUILD DONE @$(date +'%s.%N') ==="

echo "=== BAZEL TEST START @$(date +'%s.%N') ==="
set -x
bazel test \
  --noexperimental_ui \
  --build_tests_only \
  --jobs=$VCPUS \
  --local_test_jobs=$VCPUS \
  --test_timeout=1800 \
  --experimental_multi_threaded_digest \
  --sandbox_tmpfs_path=/tmp \
  -- \
  $TEST_TARGETS \
  $TEST_BLACKLIST
set +x
echo "=== BAZEL TEST DONE @$(date +'%s.%N') ==="

echo "=== BAZEL CLEAN START @$(date +'%s.%N') ==="
set -x
bazel clean --expunge
set +x
echo "=== BAZEL CLEAN DONE @$(date +'%s.%N') ==="

echo "=== BENCHMARK COMPLETE ==="

exit 0
