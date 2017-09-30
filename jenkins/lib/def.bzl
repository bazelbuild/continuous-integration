# Copyright (C) 2017 The Bazel Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

def bazel_job_configuration_test(name, configs):
    """A simple test that test that all config files can be parsed."""
    native.java_test(
        name = name,
        size = "small",
        runtime_deps = [
            "//3rdparty/jvm/org/codehaus/groovy:groovy_all",
            "//3rdparty/jvm/org/hamcrest:hamcrest_all",
            "//jenkins/lib:BazelConfigurationParsingTest"],
        data = configs,
        test_class = "build.bazel.ci.BazelConfigurationParsingTest",
    )
