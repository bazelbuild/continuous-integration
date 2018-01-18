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
 * A step for our custom git, the normal git step does not allow to recurse
 * into submodule, nor to specify a custom refs.
 *
 * Params:
 *   repository (mandatory): the name of the repository to fetch
 *   branch (default to master): the name of the branch to checkout (can be a hash too)
 *   refspec (default to refs/heads/*): the list of refs to fetch
 */
def call(config = [:]) {
  config["branch"] = config.get("branch", "master")
  config["refspec"] = config.get("refspec", "+refs/heads/*:refs/remotes/origin/*")
  if (!("repository" in config)) {
    error("recursiveGit needs a repository parameter")
  }
  def branch = config.branch.matches('^([a-f0-9]+|(origin|refs)/.*)$') ? config.branch : ("*/" + config.branch)
  checkout(scm: [$class: 'GitSCM',
                 branches: [[name: branch]],
                 doGenerateSubmoduleConfigurations: false,
                 extensions: [[$class: "SubmoduleOption",
                               disableSubmodules: false,
                               parentCredentials: false,
                               recursiveSubmodules: true,
                               reference: "",
                               trackingSubmodules: false],
                              [$class: 'CleanBeforeCheckout']],
                 submoduleCfg: [],
                 userRemoteConfigs: [[url: config.repository, refspec: config.refspec]]],
           poll: true)
}
