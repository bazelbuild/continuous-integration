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

# Simple test that run jenkins and verify that some content is there.

# So that the docker incremental loader knows where the runfiles are.
export PYTHON_RUNFILES="${PYTHON_RUNFILES:-${BASH_SOURCE[0]}.runfiles}"
cd "${PYTHON_RUNFILES}"
PYTHON_RUNFILES="${PWD}"

source "${PYTHON_RUNFILES}/io_bazel_ci/jenkins/test/test-support.sh"
setup

test_ok_status "/job/Global/job/pipeline/"
test_ok_status "/job/Github-Trigger/"
test_ok_status "/job/CR/job/gerrit-verifier"
test_ok_status "/job/CR/job/global-verifier"

test_ok_status "/job/rules_closure/"
test_ok_status "/job/PR/job/rules_closure/"
test_ok_status "/job/Global/job/rules_closure/"

test_ok_status "/job/bazel-tests/"
test_ok_status "/job/PR/job/bazel-tests/"
test_ok_status "/job/CR/job/bazel-tests/"
test_ok_status "/job/Global/job/bazel-tests/"

teardown
