#!/bin/bash
#
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

cat >/etc/cron.daily/cleanup_bazel_installs <<'EOF'
#!/bin/bash
# Clean-up bazel installs
BAZEL_INSTALLER_PREFIX="/home/ci/.cache/bazel/_bazel_ci/install"

ctime=$(date +%s)
for f in ${BAZEL_INSTALLER_PREFIX}/*; do
  mtime=$(stat -c "%X" $f/_embedded_binaries/install_base_key)
  if (( $ctime - $mtime > 86400*14 )); then
    # The last modification time is older than 14 days, delete.
    rm -fr $f
  fi
done
EOF

chmod +x /etc/cron.daily/cleanup_bazel_installs
