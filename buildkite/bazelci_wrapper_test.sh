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
# Description: Test for the shell bazelci.sh wrapper.

TEST_NAME=bazelci_wrapper_test
CLEANUP=${CLEANUP:-1}
test_scratch=
git_root=$(git rev-parse --show-toplevel)
export BAZELCI_QUIET=1
export BAZELCI_PYTHON=python3

function set_up() {

  test_scratch=$(mktemp -d -p /tmp bazelci_wrapper_test.XXXX)
  echo "[$TEST_NAME] Created scratch dir: $test_scratch"
  mkdir -p $test_scratch/master/buildkite
  # Write a fake bazelci.py that just returns the args.
  cat > $test_scratch/master/buildkite/bazelci.py << EOT
import sys

# Skip argv[0] (the program name)
for arg in sys.argv[1:]:
  print(arg)
EOT
}

function cleanup() {
  if [[ "$CLEANUP" -eq 0 ]]; then
    return
  fi
  (
    set -euo pipefail
    echo "[$TEST_NAME] Cleaning up test scratch dir: $test_scratch" 1>&2 
    rm -rf "$test_scratch"
  )
}

function test_args_returned() {
  BAZELCI_BASE_URL="file://$test_scratch" $git_root/buildkite/bazelci.sh arg1 arg2 arg3 > $test_scratch/$FUNCNAME.log

  # Create the golden file
  cat > $test_scratch/$FUNCNAME.golden.log << EOT
arg1
arg2
arg3
EOT
  # Check that the test output matches the golden
  diff $test_scratch/{$FUNCNAME.golden,$FUNCNAME}.log
}

function test_real_download() {
  $git_root/buildkite/bazelci.sh --help > /dev/null
}

function main() {
  set_up
  local tests=$(declare -F | awk '{print $NF}' | grep "^test_")
  for t in $tests; do
    # Execute the test in a subshell with runtime error checking.
    (
      set -euo pipefail
      $t
    )
    local rc=$?
    if [[ "$rc" -eq 0 ]]; then
      echo "[$TEST_NAME] $t PASSED"
    else
      echo "[$TEST_NAME] $t FAILED"
      failed="$t $failed"
    fi
  done

  if [[ ! -z "$failed" ]]; then
    # If the failed test list is non-empty
    echo "FAILED tests: $failed"
    exit 1
  else
    echo "ALL TESTS PASSED"
  fi
  exit 0
}

trap cleanup EXIT
main
