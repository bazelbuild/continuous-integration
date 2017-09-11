// Copyright (C) 2017 The Bazel Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import build.bazel.ci.BazelUtils

/**
 * This define a Jenkins step "bazelJob" that write a rc file, execute shell configuration steps,
 * run build and test with bazel and publish the XML reports.
 * Each arguments is set by a variable in the body of the step and the list of possible arguments
 * is:
 *   - binary: the path to the bazel binary
 *   - targets: list of targets to build
 *   - tests: list of targets to test
 *   - configuration: list of shell step to configure the project
 *   - build_opts, test_opts: option for build and test (build options also applies for tests)
 *   - extra_bazelrc: extraneous content for the rc file, will go after all other options.
 *        Generally to be provided as a parameter of the job.
 *   - stage_name: Name of the stage, for prefixing substages
 */
def call(config = [:]) {
  config["binary"] = config.get("binary", "bazel")
  config["targets"] = config.get("targets", ["//..."])
  config["tests"] = config.get("tests", ["//..."])
  config["configuration"] = config.get("configuration", [])
  config["build_opts"] = config.get("build_opts", [])
  config["test_opts"] = config.get("test_opts", [])
  config["startup_opts"] = config.get("startup_opts", [])
  config["extra_bazelrc"] = config.get("extra_bazelrc", "")
  config["stage_name"] = config.get("stage_name", "")

  // Now configure the utility class
  def utils = new BazelUtils();
  utils.bazel = config.binary
  utils.script = this;

  // And now the various stage
  def stage_prefix = config.stage_name.isEmpty() ? "" : "[${config.stage_name}] "
  utils.writeRc(config.build_opts, config.test_opts, config.startup_opts, config.extra_bazelrc)
  stage("${stage_prefix}Bazel version") {
    utils.bazelCommand("version")
  }

  if(!config.configuration.isEmpty()) {
    stage("${stage_prefix}Configuration") {
      utils.commandWithBazelOnPath(config.configuration.join("\n"))
    }
  }

  stage("${stage_prefix}Build") {
    utils.build(config.targets)
  }

  try {
    stage("${stage_prefix}Tests") {
      utils.test(config.tests)
    }
  } finally {
    stage("${stage_prefix}Results") {
      utils.testlogs("tests-${config.stage_name.replaceAll(',', '-')}")
    }
  }
}
