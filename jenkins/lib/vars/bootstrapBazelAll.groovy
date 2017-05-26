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

import build.bazel.ci.BazelConfiguration

// A step to bootstrap bazel on several platforms
def call(config = [:]) {
  def variation = config.get("variation", "")
  def repository = config.get("repository", "https://bazel.googlesource.com/bazel")
  def branch = config.get("branch", "master")
  def refspec = config.get("refspec", "+refs/heads/*:refs/remotes/origin/*")
  def configuration = config.get("configuration", "")
  def restrict_configuration = config.get("restrict_configuration", [:])

  def jobs = [:]
  def flattenConfigurations = BazelConfiguration.flattenConfigurations(
    BazelConfiguration.parse(config.configuration), config.restrict_configuration)

  // Avoid serialization
  def entrySet = flattenConfigurations.entrySet().toArray()
  def values = []
  def keys = []
  for (int k = 0; k < entrySet.length; k++) {
    values << entrySet[k].value
    keys << entrySet[k].key
  }
  entrySet = null
  config = null
  flattenConfigurations = null

  for (int k = 0; k < values.size; k++) {
    def key = keys[k]
    def value = values[k]
    def name = "node=${key.node},variation=${key.variation}"
    jobs[name] = { ->
      stage("Bootstrapping on ${name}") {
        bootstrapBazel(repository: repository,
                       branch: branch,
                       refspec: refspec,
                       node: key.node,
                       variation: key.variation,
                       archive: value.get("archive"),
                       stash: value.get("stash"),
                       targets: value.get("targets", []),
                       opts: value.get("opts", []))
      }
    }
  }

  // The actual job
  parallel jobs
}
