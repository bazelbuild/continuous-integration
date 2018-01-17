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

private def ensureGpgSecretKeyImported() {
  sh '''#!/bin/bash
echo "Import GPG Secret key"
(gpg --list-secret-keys | grep "${APT_GPG_KEY_ID}" > /dev/null) || \\
  gpg --allow-secret-key-import --import "${APT_GPG_KEY_PATH}"
# Make sure we use stronger digest algorithm.
# We use reprepro to generate the debian repository,
# but there is no way to pass flags to gpg using reprepro, so writting it into
# ~/.gnupg/gpg.conf
(grep "digest-algo sha256" ~/.gnupg/gpg.conf > /dev/null) || \\
  echo "digest-algo sha256" >> ~/.gnupg/gpg.conf
'''
}

// Generate the SHA-256 checksum and the GPG signature for a list of artifacts.
// Returns a new list of artifacts that include the generated checksum and signature files.
private def signArtifacts(files) {
  def result = []
  def script = []
  for (def file : files) {
    script <<= "echo 'Signing ${file}'"
    script <<= "(cd \"\$(dirname '${file}')\" && sha256sum \"\$(basename '${file}')\") > '${file}.sha256'"
    script <<= "gpg --no-tty --detach-sign -u \"\${APT_GPG_KEY_ID}\" '${file}'"
    result <<= file
    result <<= "${file}.sha256"
    result <<= "${file}.sig"
  }
  sh "#!/bin/bash \n${script.join '\n'}"
  return result
}

@NonCPS
private def listArtifacts(ws, dir, excludes) {
  return JenkinsUtils.list(env, "${ws}/${dir}", excludes).collect { "${dir}/${it}" }
}

private def listStashes(configuration) {
  def result = []
  def conf = BazelConfiguration.flattenConfigurations(
    BazelConfiguration.parse(configuration))
  for (k in conf.keySet()) {
    if ("stash" in conf[k] || "archive" in conf[k]) {
      result.add("bazel--node=${k.node}")
    }
  }
  return result
}

// A step that push a release for Bazel.
def call(params = [:]) {
  // Parameters
  def r_name = params.name
  def bucket = params.get("bucket", "bazel")
  def release_script = params.get("release_script", "source scripts/ci/build.sh; deploy_release")
  def email_script = params.get("email_script", "source scripts/ci/build.sh; generate_email")
  def repository = params.get("repository", "https://github.com/bazelbuild/bazel")
  def replyTo = params.get("replyTo", "bazel-ci@googlegroups.com")

  def ws = pwd()

  // Save the build log
  JenkinsUtils.saveLog(env, currentBuild, "${ws}/build.log")

  // unstash all the things
  dir("artifacts") {
    def stashNames = listStashes(params.configuration)
    for (def stashName : stashNames) {
      unstash stashName
    }
  }
  def artifacts = listArtifacts(ws, "artifacts", params.get("excludes", []))

  // Now the actual release
  withEnv(["GCS_BUCKET=${bucket}",
           "GIT_REPOSITORY_URL=${repository}",
           "GITHUB_TOKEN=${readFile(env.GITHUB_TOKEN_FILE).trim()}",
           "APT_GPG_KEY_ID=${readFile(env.APT_GPG_KEY_ID_FILE).trim()}",
           // TODO(dmarting): hack to work with release_to_apt(), we should get rid of it.
           "tmpdir=${ws}/artifacts/node=linux-x86_64"]) {
    // Sign artifacts
    ensureGpgSecretKeyImported()
    def artifact_list = signArtifacts(artifacts)

    // Release
    sh "#!/bin/bash\n${release_script} build.log ${artifact_list.join ' '}"

    // Send email announcement
    stage("Announcement mail") {
      def email = sh(script: "bash -c '${email_script}'", returnStdout: true)
      echo "Mail to: ${email}"
      if (r_name.contains("test")) {
        echo "Test release, skipping announcement mail."
      } else {
        def splittedEmail = email.split("\n", 3)
        mail(subject: splittedEmail[1],
             to: splittedEmail[0],
             replyTo: replyTo,
             body: splittedEmail[2])
      }
    }
  }
}
