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

import build.bazel.ci.JenkinsUtils
import build.bazel.ci.BazelConfiguration

// A step that push a release for Bazel.
def call(params = [:]) {
  def r_name = params.name
  def stashes = params.get("stashes",
                           { conf -> "bazel--node=${conf.node}--variation=${conf.variation}" })
  def bucket = params.get("bucket", "bazel")
  def release_script = params.get("script", "source scripts/ci/build.sh; bazel_release")
  def repository = params.get("repository", "https://github.com/bazelbuild/bazel")
  def replyTo = params.get("replyTo", "bazel-ci@googlegroups.com")
  // unstash all the things
  def conf = BazelConfiguration.flattenConfigurations(
    BazelConfiguration.parse(params.configuration),
    params.restrict_configuration).keySet().toArray()
  for (int k = 0; k < conf.length; k++) {
    def stashName = stashes(conf[k])
    if (stashName) {
      unstash stashName
    }
  }
  // Delete files we do not need
  if ("excludes" in params) {
    sh "rm -f ${params.excludes}"
  }
  // Now the actual release
  withEnv(["GCS_BUCKET=${bucket}",
           "GIT_REPOSITORY_URL=${repository}"]) {
    JenkinsUtils.saveLog(env, currentBuild, "${pwd()}/build.log")
    sh '''#!/bin/bash
# Credentials should not be displayed on the command line
export GITHUB_TOKEN="$(cat "$GITHUB_TOKEN_FILE")"
export APT_GPG_KEY_ID="$(cat "${APT_GPG_KEY_ID_FILE}")"

args=()
# TODO(dmarting): Add build.log to the list of artifacts to deploy
for i in node=*; do
  for j in $i/variation=*; do
    args+=("$(echo $i | cut -d = -f 2)" "$j")
  done
done

set -x
''' + release_script + ''' "${args[@]}"
echo "${RELEASE_EMAIL_RECIPIENT}" | tee output/ci/recipient
echo "${RELEASE_EMAIL_SUBJECT}" | tee output/ci/subject
echo "${RELEASE_EMAIL_CONTENT}" | tee output/ci/content
'''
    if (r_name.contains("test")) {
      echo "Test release, skipping announcement mail"
    } else {
      stage("Announcement mail") {
        mail(subject: JenkinsUtils.readFile(env, "output/ci/subject"),
             to: JenkinsUtils.readFile(env, "output/ci/recipient"),
             replyTo: replyTo,
             body: JenkinsUtils.readFile(env, "output/ci/content"))
      }
    }
  }
}
