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

// This pipeline control a global test for Bazel:
//   - Bootstrap bazel and do some basic tests
//   - Deploy the artifacts (site, releases) and send mails
//   - Run all downstream job

stage("Startup global test") {
  echo "Running global test for branch ${params.BRANCH} (refspec: ${params.REFSPEC})"
}

notifyStatus(mail_recipient) {
  // First we bootstrap bazel on all platform
  stage("Bootstrap on all platforms") {
    bootstrapBazelAll(branch: params.BRANCH,
                      refspec: params.REFSPEC,
                      email: mail_recipient,
                      configuration: json_config,
                      restrict_configuration: restrict_configuration)
  }

  // Some basic tests
  // TODO(dmarting): maybe we want to run it in parallel of other jobs?
  stage("Test that all sources are in the //:srcs filegroup") {
    node("linux-x86_64") {
      recursiveGit(repository: "https://bazel.googlesource.com/bazel",
                   refspec: params.REFSPEC,
                   branch: params.BRANCH)
      def bazel = fetchBazel("latest", "linux-x86_64")
      sh(script: "./compile.sh srcs ${bazel}")
    }
  }
}


// Deployment steps
if(params.BRANCH.matches('^(.*/)master$')) {
  stage("Push website") {
    node("deploy") {
      recursiveGit(repository: "https://bazel.googlesource.com/bazel",
                   refspec: params.REFSPEC,
                   branch: params.BRANCH)
      unstash "bazel--node=linux-x86_64--variation="
      sh script: '''#!/bin/bash
. scripts/ci/build.sh
for i in $(find input -name \'*.bazel.build.tar\'); do
  build_and_publish_site "$i" "$(basename $i .tar)" "build"
done
for i in $(find input -name \'*.bazel.build.tar.nobuild\'); do
  build_and_publish_site "$i" "$(basename $i .tar.nobuild)" "nobuild"
done
'''
    }
  }
} else if(params.BRANCH.matches('^refs/((heads/release-)|(tags/)).*$')) {
  def r_name = ""
  node("deploy") {
    r_name = sh(script: "bash -c 'source scripts/release/common.sh; get_full_release_name'",
                returnStdout: true)
    if (!r_name.isEmpty()) {
      stage("Push release") {
        // unstash all the things
        def conf = BazelConfiguration.flattenConfigurations(
          BazelConfiguration.parse(json_config), restrict_configuration).keySet().toArray()
        for (int k = 0; k < entrySet.size; k++) {
          unstash "bazel--node=${conf[k].node}--variation=${conf[k].variation}"
        }
        // Delete files we do not need
        sh "rm -f node=*/variation=*/bazel node=*/variation=*/*.bazel.build.tar*"
        // Now the actual release
        withEnv(["GCS_BUCKET=bazel",
                 "GIT_REPOSITORY_URL=https://github.com/bazelbuild/bazel"]) {
          dir("output/ci") { -> }
          sh '''#!/bin/bash
# Credentials should not be displayed on the command line
export GITHUB_TOKEN="$(cat "$GITHUB_TOKEN_FILE")"
export APT_GPG_KEY_ID="$(cat "${APT_GPG_KEY_ID_FILE}")"
source scripts/ci/build.sh

args=()
for i in node=*; do
  for j in $i/variation=*/*; do
    args+=("$(echo $i | cut -d = -f 2)" "$j")
done

bazel_release "${args[@]}"
echo "${RELEASE_EMAIL_RECIPIENT}" | tee output/ci/recipient
echo "${RELEASE_EMAIL_SUBJECT}" | tee output/ci/subject
echo "${RELEASE_EMAIL_CONTENT}" | tee output/ci/content
'''
          if (r_name.contains("test")) {
            echo "Test release, skipping announcement mail"
          } else {
            stage("Announcement mail") {
              mail(subject: readFile("output/ci/subject"),
                   to: readFile("output/ci/recipient"),
                   replyTo: "bazel-ci@googlegroups.com",
                   body: readFile("output/ci/content"))
            }
          }
        }
      }
    }
  }
  // TODO(dmarting): trigger bazel install everywhere in case of release.
}

// Then we run all the job in the Global folder but myself
stage("Test downstream jobs") {
  runAll(folder: "Global",
         parameters: [
           [$class: 'TextParameterValue',
            name: 'EXTRA_BAZELRC',
            value: "${params.EXTRA_BAZELRC}"],
           [$class: 'StringParameterValue',
            name: 'BRANCH',
            value: "${params.BRANCH}"],
           [$class: 'StringParameterValue',
            name: 'REFSPEC',
            value: "${params.REFSPEC}"]
         ])
}
