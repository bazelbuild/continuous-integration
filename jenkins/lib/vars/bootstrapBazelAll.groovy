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

// A step to bootstrap bazel on several platforms
def call(config = [:]) {
  def repository = config.get("repository", "https://bazel.googlesource.com/bazel")
  def branch = config.get("branch", "master")
  def refspec = config.get("refspec", "+refs/heads/*:refs/remotes/origin/*")
  def configuration = config.get("configuration", "")

  def jobs = [:]
  // Convert to an array to avoid serialization issue with Jenkins
  def entrySet = readConfiguration(files: ["scripts/ci/bootstrap.json"],
                                   repository: config.repository,
                                   branch: config.branch,
                                   refspec: config.refspec,
                                   default_configuration: config.get("configuration", null)
                                  ).entrySet().toArray()
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
    def name = build.bazel.ci.BazelConfiguration.descriptorToString(key)
    jobs[name] = { ->
      stage("Bootstrapping on ${name}") {
        bootstrapBazel(repository: repository,
                       branch: branch,
                       refspec: refspec,
                       node: key.node,
                       archive: value.get("archive"),
                       stash: value.get("stash"),
                       targets: value.get("targets", []),
                       configure: value.get("configure", []),
                       opts: value.get("opts", []))
      }
    }
  }

  // The actual job
  parallel jobs
}
