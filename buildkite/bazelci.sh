#!/bin/bash
#
# Copyright 2026 The Bazel Authors. All rights reserved.
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
# 
# Description: A transparent wrapper around bazelci.py.
#
# Currently this just download bazelci.py with the existing boilerplate
# commands and passes args down to the python script. In the future,
# it will also download bazelci.py dependencies as we split the logic
# into more specialized modules.

set -euo pipefail

# Constants
BAZELCI_PYTHON="${BAZELCI_PYTHON:-python3.6}"
BAZELCI_BASE_URL="${BAZELCI_BASE_URL:-https://raw.githubusercontent.com/bazelbuild/continuous-integration}"
BAZELCI_BRANCH="${BAZELCI_BRANCH:-master}"
BAZELCI_PY_URL="${BAZELCI_BASE_URL}/${BAZELCI_BRANCH}/buildkite/bazelci.py"
BAZELCI_QUIET="${BAZELCI_QUIET:-0}"

# Create a scratch space
scratch=$(mktemp -d -p /tmp bazelci.XXXX)

# Helper functions
function cleanup() {
  if [[ "$BAZELCI_QUIET" -eq 0 ]]; then
    echo "[bazelci] Cleaning up bazelci scratch space: $scratch" 1>&2
  fi
  rm -rf "$scratch"
}

trap cleanup EXIT

# Download bazelci.py (and in the future, its dependencies).
cd $scratch
curl -sS "$BAZELCI_PY_URL?"$(date +%s) -o bazelci.py

# Execute the script"
"$BAZELCI_PYTHON" bazelci.py "$@"

