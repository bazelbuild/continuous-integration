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
import build.bazel.ci.GerritUtils
import build.bazel.ci.JenkinsUtils

/**
 * Define a step "gerritReview" that wrap a build to be a "Gerrit review": the change
 * will be commented according to the result of the build and the verified bit will be
 * updated.
 * except if that argument is empty (in which case the body is executed directly).
 */
def call(String server, String cookiesFile, String reviewer, changeNum, branch, Closure body) {
  GerritUtils gerrit = new GerritUtils(server, cookiesFile, reviewer)
  def url = gerrit.url(changeNum)
  this.gerritBuild = currentBuild
  stage("Start Gerrit review") {
    echo "Reviewing change ${url} (${branch})"
    gerrit.addReviewer(changeNum)
    gerrit.comment(changeNum, branch,
		   "Starting build at ${JenkinsUtils.getBlueOceanUrl(currentBuild)}")
  }
  def config = [gerritBuild: currentBuild]
  try {
    body.delegate = config
    body()
  } finally {
    def result = config.gerritBuild.result == null ? "SUCCESS" : config.gerritBuild.result
    def verified = result == "SUCCESS" ? "+" : "-"
    echo "Setting ${verified}Verified to change ${url} after build returned ${result}"
    gerrit.review(changeNum, branch, result == "SUCCESS" ? 1 : -1,
                  "Build ${JenkinsUtils.getBlueOceanUrl(config.gerritBuild)} finished with status ${result}")
  }
}
