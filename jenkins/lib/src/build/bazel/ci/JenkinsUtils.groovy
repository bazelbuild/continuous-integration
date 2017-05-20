// Copyright (C) 2017 The Bazel Authors.
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

package build.bazel.ci

/**
 * This class provide utility methods of the Jenkins API
 */
class JenkinsUtils {
  /** A list of regex aliases to know that ubuntu is linux */
  private static def NODE_ALIASES = [
    "ubuntu.*": "linux-x86_64",
    "docker.*": "linux-x86_64",
    "darwin.*": "darwin-x86_64",
  ]

  /** Normalize the node label into a compatible platform */
  // TODO(dmarting): does that really belongs here?
  @NonCPS
  static def normalizeNodeLabel(node_label) {
    for (e in NODE_ALIASES) {
      if (node_label.matches(e.key)) {
        return e.value
      }
    }
    return node_label
  }

  /** Returns the list of all slave' names */
  @NonCPS
  static def nodeNames() {
    return jenkins.model.Jenkins.instance.nodes.collect { node -> node.name }
  }

  /** Returns the list of job in the folder `folderName` (empty or null for top folder). */
  @NonCPS
  private static def folderJobs(folderName) {
    if (folderName == null || folderName.isEmpty()) {
      return jenkins.model.Jenkins.instance.items
    } else {
      return jenkins.model.Jenkins.instance.getItemByFullName(folderName).getAllJobs()
    }
  }

  /**
   * Returns the list of names of jobs in the folder `folderName` (empty or null for the
   * top folder).
   */
  @NonCPS
  static def jobs(folderName) {
    return folderJobs(folderName).collect { job -> job.name }
  }

  /**
   * Returns the list of names of jobs in the folder `folder` (empty or null for the top
   * folder) whose description contains the string `descr`
   */
  @NonCPS
  static def jobsWithDescription(folder, descr) {
    def items = jenkins.model.Jenkins.instance.items
    def jobs = folderJobs(folder)
    return jobs.findAll {
      job -> job.description != null && job.description.contains(descr) }.collect {
      job -> job.name }
  }

  /** Returns the last build of a job in a specific folder */
  @NonCPS
  static def getLastRun(folder, job) {
    def j = folderJobs(folder).find { it -> it.name.equals(job) }
    if (j != null) {
      def run = j.getLastCompletedBuild()
      if (run != null) {
        return new org.jenkinsci.plugins.workflow.support.steps.build.RunWrapper(run, false)
      }
    }
    return null
  }

  /**
   * A utility method that look for an artifact matching a pattern in upstream
   * builds.
   */
  @NonCPS
  static def findAndCopyUpstreamArtifacts(run, pattern) {
    def build = findLastBuildWithUpstream(run.rawBuild)
    if (build == null) {
      return null
    }
    return _findAndCopyUpstreamArtifacts(build.getCauses(), pattern)
  }

  @NonCPS
  private static def _findAndCopyUpstreamArtifacts(causes, pattern) {
    for (cause in causes) {
      if (cause instanceof Cause.UpstreamCause) {
        def upstreamRun = cause.getUpstreamRun()
        def artifacts = upstreamRun.getArtifacts()
        for (artifact in artifacts) {
          if (artifact.toString().matches(pattern)) {
            return [artifactPath: artifact.toString(),
                    artifactName: artifact.getFileName(),
                    upstreamBuild: cause.getUpstreamBuild(),
                    upstreamProject: cause.getUpstreamProject()]
          }
        }
        def res = _findAndCopyUpstreamArtifacts(cause.upstreamCauses, pattern)
        if (res != null && !res.isEmpty()) {
          return res;
        }
      }
    }
    return null
  }

  /**
   * Find the latest build that was run by upstream.
   * In case of re-run, the current build will not be triggered by upstream project.
   * In that case we want to look at build history to fetch the latest one that was build
   * with upstream.
   */
  @NonCPS
  private static def findLastBuildWithUpstream(run) {
    while (run != null) {
      if (run.getCauses().any { it.class.toString().contains("UpstreamCause") }) {
        return run
      }
      run = run.getPreviousBuild()
    }
    return run
  }
}
