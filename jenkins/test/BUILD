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

package(default_visibility = ["//jenkins:__subpackages__"])

sh_library(
    name = "common",
    srcs = ["common.sh"],
    data = [
        "//jenkins:deploy.docker",
        "//jenkins:jenkins-test",
        "//jenkins:ubuntu-docker.docker",
    ],
)

sh_binary(
    name = "test",
    srcs = ["test.sh"],
    data = [
        "//jenkins:deploy.docker",
        "//jenkins:jenkins-test",
        "//jenkins:ubuntu-docker.docker",
    ],
    deps = [":common"],
)

sh_library(
    name = "test-support",
    srcs = ["test-support.sh"],
    deps = [":common"],
)

sh_test(
    name = "test_url_answer",
    size = "large",
    srcs = ["test_url_answer.sh"],
    # TODO(dmarting): why the sh_library data does not get shipped in the sh_test data?
    data = [
        "//jenkins:deploy.docker",
        "//jenkins:jenkins-test",
        "//jenkins:ubuntu-docker.docker",
        "@docker//:docker",
    ],
    deps = [":test-support"],
)
