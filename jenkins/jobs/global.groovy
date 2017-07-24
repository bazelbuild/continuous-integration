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
    bootstrapBazelAll(repository: params.REPOSITORY,
                      branch: params.BRANCH,
                      refspec: params.REFSPEC,
                      email: mail_recipient,
                      configuration: json_config,
                      restrict_configuration: restrict_configuration)
  }

  // Some basic tests
  // TODO(dmarting): maybe we want to run it in parallel of other jobs?
  stage("Test that all sources are in the //:srcs filegroup") {
    machine("linux-x86_64") {
      recursiveGit(repository: params.REPOSITORY,
                   refspec: params.REFSPEC,
                   branch: params.BRANCH)
      def bazel = bazelPath("latest", "linux-x86_64")
      sh(script: "./compile.sh srcs ${bazel}")
    }
  }
}


// Deployment steps
def is_master = params.BRANCH.matches('^(.*/)?master$')
def is_rc = params.BRANCH.matches('^(refs/heads/)?release-.*$')
def is_release = params.BRANCH.matches('^refs/tags/.*$')
if(is_master || is_rc | is_release) {
  stage(is_master ? "Push website" : "Push release") {
    machine("deploy") {
      recursiveGit(repository: params.REPOSITORY,
                   refspec: params.REFSPEC,
                   branch: params.BRANCH)
      if (is_master) {
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
      } else {
        def r_name = sh(script: "bash -c 'source scripts/release/common.sh; get_full_release_name'",
                        returnStdout: true).trim()
        if (!r_name.isEmpty()) {
          pushRelease(name: r_name,
                      configuration: json_config,
                      restrict_configuration: restrict_configuration,
                      excludes: ["**/*.bazel.build.tar*", "**/bazel", "**/bazel.exe"])
          if (is_release) {
            stage("Install new release on all nodes") {
              build(job: "install-bazel", wait: false, propagate: false)
            }
          }
        }
      }
    }
  }
}

// Then we run all jobs in the Global folder except the global pipeline job (the current job).
report = null
stage("Test downstream jobs") {
  report = runAll(folder: "Global",
         parameters: [
           [$class: 'TextParameterValue',
            name: 'EXTRA_BAZELRC',
            value: "${params.EXTRA_BAZELRC}"],
           [$class: 'StringParameterValue',
            name: 'REPOSITORY',
            value: "${params.REPOSITORY}"],
           [$class: 'StringParameterValue',
            name: 'BRANCH',
            value: "${params.BRANCH}"],
           [$class: 'StringParameterValue',
            name: 'REFSPEC',
            value: "${params.REFSPEC}"]
         ],
         excludes: ["pipeline", currentBuild.getProjectName()])
}

stage("Publish report") {
  reportAB report: report, name: "Downstream projects"
  if (mail_recipient) {
    mail(subject: "Global tests #${currentBuild.number} finished with status ${currentBuild.result}",
         body: """A global tests has just finished with status ${currentBuild.result}.

You can find the report at ${currentBuild.getAbsoluteUrl()}Downstream_projects/.
""",
         to: mail_recipient)
  }
}
