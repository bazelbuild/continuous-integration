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

/**
 * A step that returns the path of a specific version of the bazel binary. If that version is
 * set to "custom", it will for look for the bazel binary in the list of artifacts transmitted
 * by upstream job (not yet implemented). In the other case, it looks for bazel in a well
 * known location.
 */
def call(String bazel_version, String node_label) {
  def bazel = node_label.startsWith("windows") ?
              "c:\\bazel_ci\\installs\\${bazel_version}\\bazel.exe" :
              "${env.HOME}/.bazel/${bazel_version}/bin/bazel"

  // Grab bazel
  if (bazel_version.startsWith("custom")) {
    // A custom version can be completed with a variation, e.g. custom-jdk7, extract it
    def variation = bazel_version.substring(6)
    node_label = JenkinsUtils.normalizeNodeLabel(node_label)
    def cause = JenkinsUtils.findAndCopyUpstreamArtifacts(
      currentBuild,
      "^node=${node_label}/variation=${variation}/bazel(\\.exe)?\$")

    if (cause == null) {
      error("Failed to find upstream cause while asked to build with custom Bazel")
    }

    def ws = pwd()
    def targetPath = "${ws}/.bazel"
    echo "Using Bazel binary from upstream project ${cause.upstreamProject} build #${cause.upstreamBuild} at path ${cause.artifactPath}"
    dir(".bazel") { deleteDir() }
    step([$class: 'CopyArtifact',
          filter: cause.artifactPath,
          fingerprintArtifacts: true,
          flatten: true,
          projectName: cause.upstreamProject,
          selector: [$class: 'SpecificBuildSelector',
                     buildNumber: "${cause.upstreamBuild}"],
          target: targetPath])
    bazel = targetPath + "/" + cause.artifactName
  } else {
    echo "Using released version of Bazel at ${bazel}"
  }

  return bazel
}
