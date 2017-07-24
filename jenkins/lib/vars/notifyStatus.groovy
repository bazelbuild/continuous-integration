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

/**
 * Define a step "notifyStatus" to notify the status of the
 * current build. Currently only send a mail to "recipients".
 */
def call(String recipients, Closure body) {
  try {
    body()
  } finally {
    stage("Sending results") {
      if (recipients != null && !recipients.isEmpty()) {
        node("deploy") {
          // Why do we even need a node to send a mail?
          // TODO(dmarting): maybe use mailext?
          echo "Sending mail to ${recipients.join ','}"
          step([$class: 'Mailer',
                notifyEveryUnstableBuild: false,
                recipients: recipients,
                sendToIndividuals: false])
        }
      } else {
        echo "Mail notifications disabled"
      }
    }
  }
}
