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

import build.bazel.ci.BazelUtils

@NonCPS
def createCopyCommand(rootDir, toCopy, release_name) {
  def replaceFn = { o -> o.replace("%{release_name}", release_name) }
  def replacements = toCopy.collect(
    { e ->
      (e.value instanceof List) ?
      e.value.collect { it -> "${e.key} ${replaceFn(it)}" }
      : "${e.key} ${replaceFn(e.value)}"
    }).flatten()
  return replacements.collect({ e -> "cp ${rootDir}/${e}" }).join("\n")
}

// A step to bootstrap bazel on one platform
def call(config = [:]) {
  def repository = config.get("repository", "https://bazel.googlesource.com/bazel")
  def branch = config.get("branch", "master")
  def refspec = config.get("refspec", "+refs/heads/*:refs/remotes/origin/*")
  def targets = config.get("targets", [])

  machine(config.node) {
    def utils = new BazelUtils()
    def release_name = ""
    def isWindows = !isUnix()
    utils.script = this
    utils.bazel = bazelPath("latest", config.node)
    stage("[${config.node}] clone") {
      recursiveGit(repository: repository,
                   refspec: refspec,
                   branch: branch)
    }
    stage("[${config.node}] get_version") {
      release_name =
        sh(script: "bash -c 'source scripts/release/common.sh; get_full_release_name'",
           returnStdout: true).trim()
      def opts = config.get("opts", [])
      opts <<= "--stamp"
      if (!isWindows) {
        // TODO(dmarting): Windows status command fails :/
        opts <<= "--workspace_status_command=scripts/ci/build_status_command.sh"
      }
      if (!release_name.isEmpty()) {
        opts <<= "--embed_label ${release_name}"
      }
      utils.writeRc(opts)
    }

    // Configure, if necessary
    def configuration = config.get("configure", [])
    if (!configuration.isEmpty()) {
      stage("[${config.node}] configure") {
        if (isUnix()) {
          sh "#!/bin/sh -x\n${configuration.join('\n')}"
        } else {
          bat configuration.join('\n')
        }
      }
    }

    stage("[${config.node}] bootstrap") {
      def envs = ["BUILD_BY=Jenkins",
                  "GIT_REPOSITORY_URL=${env.GIT_URL}"]
      utils.build(["//src:bazel"] + targets)
    }

    // Archive artifacts
    def toArchive = config.get("archive", [:])
    def toStash = config.get("stash", [:])
    toArchive = toArchive == null ? [:] : toArchive
    toStash = toStash == null ? [:] : toStash

    if (!toArchive.isEmpty() || !toStash.isEmpty()) {
      stage("[${config.node}] archive") {
        def rootDir = pwd()
        if (isWindows) {
          rootDir = sh(script: 'cygpath -u '+rootDir.replace("\\", "/"),
                       returnStdout: true).trim()
        }
        dir("output") {
          deleteDir()
        }
        if(!toArchive.isEmpty()) {
          dir("output/node=${config.node}") {
            sh createCopyCommand(rootDir, toArchive, release_name)
          }
          dir("output") {
            archiveArtifacts artifacts: "**", fingerprint:true
          }
        }
        if (!toStash.isEmpty()) {
          dir("output/node=${config.node}") {
            sh createCopyCommand(rootDir, toStash, release_name)
          }
        }
        dir("output") {
          stash name: "bazel--node=${config.node}"
        }
      }
    }
  }
}
