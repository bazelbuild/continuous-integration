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

/**
 * This define a Jenkins step "bazelCiJob" that use git and Bazel to test one configuration.
 * Each arguments is set by a variable in the body of the step and the list of possible arguments
 * is:
 *   - name
 *   - bazel_version is the baseline for the version of Bazel, generally a parameter for the job.
 *        If set to 'custom.*', the job will try to fetch the Bazel binary from upstream.
 *   - targets: list of targets to build
 *   - tests: list of targets to test
 *   - configuration: list of shell step to configure the project
 *   - build_opts, test_opts: option for build and test (build options also applies for tests)
 *   - extra_bazelrc: extraneous content for the rc file, will go after all other options.
 *        Generally to be provided as a parameter of the job.
 *   - build_tag_filters, test_tag_filters: tag filters to pass to bazel
 *   - workspace: a directory, relative to the root of the repository, that contains
 *        the workspace file, default to the top directory.
 *   - repository: git repository to clone.
 *   - branch: branch of the repository to clone (default: master).
 *   - refspec: specification of the references to fetch
 *   - sauce: identifier of the crendentials to connect to SauceLabs.
 *   - node_label: label of the node to run on
 */
def call(config = [:]) {
  config["bazel_version"] = config.get("bazel_version", "latest")
  config["targets"] = config.get("targets", ["//..."])
  config["tests"] = config.get("tests", ["//..."])
  config["configuration"] = config.get("configuration", [])
  config["build_opts"] = config.get("build_opts", [])
  config["test_opts"] = config.get("test_opts", [])
  config["extra_bazelrc"] = config.get("extra_bazelrc", "")
  config["build_tag_filters"] = config.get("build_tag_filters", [])
  config["test_tag_filters"] = config.get("test_tag_filters", [])
  config["workspace"] = config.get("workspace", "")
  config["repository"] = config.get("repository", "")
  config["sauce"] = config.get("sauce", "")
  config["branch"] = config.get("branch", "master")
  config["refspec"] = config.get("refspec", "+refs/heads/*:refs/remotes/origin/*")

  def prefix = "${config.node_label}"
  def workspace = ""

  def java_version = (config.bazel_version.endsWith("-jdk7")) ? "1.7" : "1.8"
  config.test_tag_filters += ["-noci", "-manual"]
  if (java_version == "1.7") {
    config.test_tag_filters += ["-jdk8"]
    prefix += "-jdk7"
    config.build_tag_filters += ["-jdk8"]
  }
  def build_options = config.build_opts + [
    "--define JAVA_VERSION=${java_version}",
    "--build_tag_filters=${config.build_tag_filters.join ','}"
  ]
  def test_options = config.test_opts + [
    "--test_tag_filters=${config.test_tag_filters.join ','}",
    "--build_tests_only",
    "-k"
  ]
  machine(config.node_label) {
    ws("workspace/${currentBuild.fullProjectName}-" +
       config.get("name", config.node_label + "-" + config.bazel_version)) {
      maybeSauce(config.sauce) {
        // Checkout the code
        echo "Checkout ${config.repository}"
        recursiveGit(repository: config.repository,
                     refspec: config.refspec,
                     branch: config.branch)

        // And build
        withEnv(["JAVA_VERSION=${java_version}"]) {
          maybeDir(config.workspace) {
            def bazel = bazelPath(config.bazel_version, config.node_label)

            bazelJob(binary: bazel,
                     build_opts: build_options,
                     test_opts: test_options,
                     extra_bazelrc: config.extra_bazelrc,
                     targets: config.targets,
                     tests: config.tests,
                     configuration: config.configuration,
                     stage_name: prefix
            )
          }
        }
      }
    }
  }
}

