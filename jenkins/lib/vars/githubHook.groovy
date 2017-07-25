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

import groovy.json.JsonSlurper

@NonCPS
private def parseGithubPayload(def payload) {
  def json = new JsonSlurper().parseText(payload)
  if (json.deleted) {
    return null
  }
  return ["branch": json.ref, "repository": json.repository.full_name, "url": json.repository.url]
}

// A step that executes a subcommand if a given payload coming from Github describe an update
// to a given branch / tag.
// Parameters:
//   - payload: the name of the parameters containing the Github webhook JSON payload.
//   - refs: a regex to match the ref that was passed.
//   - repositories: a list of allowed repositories.
// Note that the body is executed either if there is a payload and the payload matche the
// criteria or no payload was provided. The body will be passed as delegate a map containing
// the branch ref ('branch'), the repository name ('repository') and url ('url'). They will be
// null if no payload was provided.
def call(def config, Closure body) {
  def payloadName = config.get("payload", "payload")
  def refs = config.get("refs", ".*")
  def repositories = config.get("repositories", ["bazelbuild/bazel"])

  body.delegate = ["branch": null, "repository": null, "url": null]
  if (params[payloadName]) {
    def payload = parseGithubPayload(params[payloadName])
    if (payload && payload.branch.matches(refs) && payload.repository in repositories) {
      body.delegate = payload
      body()
    }
  } else {
    body()
  }
}
