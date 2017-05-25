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
}
