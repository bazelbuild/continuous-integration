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

// Automatic import in Jenkins but we need them to compile outside of Jenkins
import com.cloudbees.groovy.cps.NonCPS
import hudson.model.*
import jenkins.model.*

import hudson.FilePath
import hudson.remoting.Channel
import org.jenkinsci.plugins.workflow.support.steps.build.RunWrapper

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

  /** Returns the list of all slave' names (optionally filtering by label) */
  @NonCPS
  static def nodeNames(label = null) {
    def nodes = jenkins.model.Jenkins.instance.nodes
    if (label != null) {
      nodes = nodes.findAll { node -> label in node.labelString.split() }
    }
    return nodes.collect { node -> node.name }
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

  /** Returns the URL of the console for a job run */
  @NonCPS
  static def getConsoleUrl(RunWrapper run) {
    return "${run.absoluteUrl}console"
  }

  /** Returns the URL of the blue ocean view for a job run */
  @NonCPS
  static def getBlueOceanUrl(RunWrapper run) {
    def name = java.net.URLEncoder.encode(run.fullProjectName, "UTF-8")
    def url = new URL(run.absoluteUrl)
    def path = "/blue/organizations/jenkins/${name}/detail/${run.projectName}/${run.number}/pipeline/"
    return new URL(url.protocol, url.host, url.port, path).toString()
  }

  /** Returns the URL to the small icon for a run */
  @NonCPS
  static def getSmallIconUrl(RunWrapper run) {
    return "${Jenkins.RESOURCE_PATH}/images/16x16/${run.rawBuild.getIconColor()}.png"
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

  @NonCPS
  private static def _pruneIfOlderThan(file, timestamp) throws IOException {
    if (file.isDirectory()) {
      boolean empty = true
      for (child in file.list()) {
        if (!_pruneIfOlderThan(child, timestamp)) {
          empty = false
        }
      }
      if (empty) {
        if (file.delete()) {
          return true
        }
      }
    } else if (file.lastModified() < timestamp) {
      if (file.delete()) {
        return true
      }
    }
    return false
  }

  @NonCPS
  private static def createFilePath(env, path) {
    if (env['NODE_NAME'].equals("master")) {
        return new FilePath(path);
    } else {
        return new FilePath(Jenkins.getInstance().getComputer(env['NODE_NAME']).getChannel(), path);
    }
  }

  /** Prune file that are older than timestamp on the current node. */
  @NonCPS
  public static def pruneIfOlderThan(env, path, timestamp) {
    return _pruneIfOlderThan(createFilePath(env, path), timestamp)
  }

  /** Touch a file anywhere on the FS on the current node. */
  @NonCPS
  public static def touchFileIfExists(env, path) {
    FilePath f = createFilePath(env, path)
    def r = f.exists()
    if (r) {
      try {
        f.touch(System.currentTimeMillis())
      } catch(IOException ex) {
        // The file might be busy, especially on windows, swallowing exception
      }
    }
    return r;
  }

  /** Read a file from the node, but without reporting anything in the Jenkins UI. */
  @NonCPS
  public static def readFile(env, path) {
    return createFilePath(env, path).readToString()
  }

  /** Save the current log to a file on the current node. */
  @NonCPS
  public static void saveLog(env, RunWrapper run, path) {
    createFilePath(env, path).copyFrom(run.getRawBuild().getLogInputStream())
  }

  /** Returns the recursive list of files of a folder, ignoring some files. */
  @NonCPS
  public static def list(env, dir, excludes) {
    def directory = createFilePath(env, dir)
    def results = directory.list("**", excludes.join(","))
    def directoryUri = directory.toURI()
    return results.collect { it -> directoryUri.relativize(it.toURI()) }
  }
}
