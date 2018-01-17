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

def createJobsFromConfiguration(config, configNames, script) {
  def cfgs = []
  def name = currentBuild.projectName
  // Convert to an array to avoid serialization issue with Jenkins
  def entrySet = readConfiguration(files: [".ci/${name}.json", "scripts/ci/${name}.json"],
                                   repository: config.repository,
                                   branch: config.branch,
                                   refspec: config.refspec,
                                   default_configuration: config.configuration,
                                   restrict_configuration: config.restrict_configuration
                                  ).entrySet().toArray()
  for (int k = 0; k < entrySet.length; k++) {
    def params = entrySet[k].value
    def conf = entrySet[k].key
    def configName = build.bazel.ci.BazelConfiguration.descriptorToString(conf)
    configNames.add(configName)
    cfgs.add({ ->
        script.bazelCiJob(name: configName,
                          repository: config.repository,
                          branch: config.branch,
                          refspec: config.refspec,
                          node_label: conf["node"],
                          targets: params.get("targets", ["//..."]),
                          tests: params.get("tests", ["//..."]),
                          configuration: params.get("configure", []),
                          build_opts: params.get("build_opts", []),
                          test_opts: params.get("test_opts", []),
                          startup_opts: params.get("startup_opts", []),
                          bazel_version: config.bazel_version + conf.get("variation", ""),
                          extra_bazelrc: config.extra_bazelrc,
                          build_tag_filters: params.get("build_tag_filters", []),
                          test_tag_filters: params.get("test_tag_filters", []),
                          workspace: config.workspace,
                          sauce: config.sauce
      )
    })
  }
  entrySet = null
  return cfgs
}

/**
 * This define a Jenkins step "bazelCiConfiguredJob" that use git and Bazel
 * with various configurations given by a list of platforms and a list of variation of Bazel.
 * Each arguments is set by a variable in the body of the step and the list of possible arguments
 * is:
 *   - bazel_version is the baseline for the version of Bazel, generally a parameter for the job.
 *        If set to 'custom', the job will try to fetch the Bazel binary from upstream.
 *   - configuration: JSON configuration, see BazelConfiguration
 *   - restrict_configuration: A map of acceptable descriptor values. If provided, for each key,
 *     only the values that are in that map will generate a configuration.
 *   - extra_bazelrc: extraneous content for the rc file, will go after all other options.
 *        Generally to be provided as a parameter of the job.
 *   - workspace: a directory, relative to the root of the repository, that contains
 *        the workspace file, default to the top directory.
 *   - repository: git repository to clone.
 *   - branch: branch of the repository to clone (default: master).
 *   - refspec: specification of the references to fetch
 *   - sauce: identifier of the crendentials to connect to SauceLabs.
 *   - run_sequentially: run each configuration sequentially rather than in parallel
 */
def call(config = [:]) {
  config["bazel_version"] = config.get("bazel_version", "latest")
  config["configuration"] = config.get("configuration", "[]")
  config["restrict_configuration"] = config.get("restrict_configuration", [:])
  config["extra_bazelrc"] = config.get("extra_bazelrc", "")
  config["workspace"] = config.get("workspace", "")
  config["repository"] = config.get("repository", "")
  config["branch"] = config.get("branch", "master")
  config["refspec"] = config.get("refspec", "+refs/heads/*:refs/remotes/origin/*")
  config["sauce"] = config.get("sauce", "")
  config["run_sequentially"] = config.get("run_sequentially", false)

  // Remove special characters from bazel_version (which can be coming from a URL post):
  //   everything except [a-zA-Z0-9_-.]
  config.bazel_version = config.bazel_version.replaceAll("[^a-zA-Z0-9_\\.-]", "")

  def configs = [:]
  // Keep a list of keys of configs in configNames to workaround
  // https://issues.jenkins-ci.org/browse/JENKINS-27421
  def configNames = []
  stage("Setting-up configurations") {
    def cfgs = createJobsFromConfiguration(config, configNames, this)
    for (int i = 0; i < cfgs.size; i++) {
      configs[configNames[i]] = cfgs[i]
    }
    cfgs = null
  }


  timeout(240) {
    try {
      stage("Run configurations") {
        if (config.run_sequentially) {
          for (configName in configNames) {
            configs[configName]()
          }
        } else {
          parallel configs
        }
      }
    } catch(build.bazel.ci.BazelTestFailure ex) {
      // Do not mark the build as error with a test failure
      currentBuild.result = "UNSTABLE"
    }
  }
}
