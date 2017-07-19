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

// Inspired by https://gerrit.googlesource.com/gerrit-ci-scripts/+/master/jenkins/gerrit-verifier-flow.groovy
package build.bazel.ci

import groovy.json.JsonOutput
import groovy.json.JsonSlurper

/*
 * This is a class to communicate with Gerrit (basically add code reviews).
 *
 * All methods to talk to gerrit are NonCPS to avoid serialization issues from Jenkins
 * and make them atomic.
 */
class GerritUtils implements java.io.Serializable {
  private String server
  private String cookies
  private String reviewer
  private String reviewerEmail

  // Parse a cookie file from cURL, ignoring most of the field
  @NonCPS
  private static def loadCookiesFile(String host, String cookieFile) {
    def url = new URI(host)
    host = url.host
    try {
      String[] fileContent = new File(cookieFile).text.split("\n")
      def result = []
      for (line in fileContent) {
        if (!line.startsWith("#") && !line.isEmpty()) {
          def elements = line.split("\t")
          if (elements.length > 0 && host.endsWith(elements[0])) {
            result << "${elements[5]}=${elements[6]}"
          }
        }
      }
      return result.join("; ")
    } catch(IOException exn) {
      return []
    }
  }

  // Initialize the utilities to connect to ${server} using cookies
  // from ${cookiesFile} and user ${reviewer} as the bot user.
  def GerritUtils(String server, String cookiesFile, String reviewer) {
    this.server = server
    if (!this.server.endsWith("/")) {
      this.server += "/"
    }
    this.cookies = loadCookiesFile(server, cookiesFile)
    this.reviewer = reviewer
    def m = reviewer =~ /^.*<([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)>$/
    if (!m) {
      // This is fine to use non checked exception since it's for bubbling up
      // to jenkins
      throw new Exception(
          "Reviewer argument does not match the pattern 'Name <email@domain>'")
    }
    this.reviewerEmail = m[0][1]
  }

  // Getters
  def getServer() {
    return server
  }

  def getCookies() {
    return cookies
  }

  def getReviewer() {
    return reviewer
  }

  def getReviewerEmail() {
    return reviewerEmail
  }

  // Return the URL of a change
  def url(changeNum, patchNum = 0) {
    return patchNum ? "${this.server}#/c/${changeNum}/${patchNum}" : "${this.server}#/c/${changeNum}"
  }

  // Post a JSON payload to the given url setting the correct cookies for authentication.
  @NonCPS
  private def post(path, data) {
    def payload = JsonOutput.toJson(data)
    def url = new URL(this.server + path)
    URLConnection con = url.openConnection()
    con.setDoOutput(true)
    con.setRequestMethod("POST")
    con.setRequestProperty("Cookie", cookies)
    con.setRequestProperty("Content-Type", "application/json")
    def wr = con.getOutputStream()
    wr.write(payload.getBytes())
    wr.flush()
    wr.close()

    int responseCode = con.getResponseCode()
    return responseCode == 200
  }

  // Add the Gerrit bot as reviewer to change ${changeNum}
  @NonCPS
  def addReviewer(changeNum) {
    return post("a/changes/${changeNum}/reviewers", [reviewer: this.reviewer])
  }

  // Set a change to verified +1/-1
  // Parameters:
  //   changeNum: number of the change to mark as verified
  //   sha1: SHA-1 sum of the commit to mark as verified
  //   verified: +1/-1 value for the verified flag on Gerrit
  @NonCPS
  def review(changeNum, sha1, verified, message = null) {
    def payload = [
      labels: ["Code-Review": 0, "Verified": verified],
      notify: (verified < 0 ? "OWNER" : "NONE")
    ]
    if (message != null) {
      payload["message"] = message
    }
    return post("a/changes/${changeNum}/revisions/${sha1}/review", payload)
  }

  // Add a comment without notifying everybody on the change.
  //   buildUrl: URL of the build corresponding to that message
  //   changeNum: change to comment on
  //   sha1: SHA-1 of the commit to comment on
  //   msgPrefix: the prefix of the message, the result message will be: <msgPrefix> Bazel CI: <buildUrl>
  @NonCPS
  def comment(changeNum, sha1, message) {
    return post("a/changes/${changeNum}/revisions/${sha1}/review",
                ["message": message, "notify": "NONE"])
  }

  // Query for gerrit for a list of change and return a list of
  // changes as returned by the Gerrit API.
  // See https://gerrit-review.googlesource.com/Documentation/rest-api-changes.html#list-changes
  // Args:
  //   query: the query of changes
  //   maxChanges: maximum number of changes to return, default to 0 means no maximum
  // Returns:
  //   An object translated from JSON as returned by the list-changes operation when asked
  //   for DETAILED_LABELS and CURRENT_REVISION.
  // Note: this method is mostly for used by GerritUtils itself.
  @NonCPS
  def query(query, maxChanges = 0) {
    def url = server + "changes/?pp=0&o=DETAILED_LABELS&o=CURRENT_REVISION"
    if (maxChanges > 0) {
      url += "&n=${maxChanges}"
    }
    url += "&q=${java.net.URLEncoder.encode(query.toString())}"
    def changes = new URL(url).getText().substring(5)
    def jsonSlurper = new JsonSlurper()
    return jsonSlurper.parseText(changes)
  }

  @NonCPS
  def removeVote(changeNumber, label, reviewer) {
    def rev = java.net.URLEncoder.encode(reviewer.toString())
    this.post("a/changes/${changeNumber}/reviewers/${rev}/votes/${label}/delete",
              ["notify": "NONE"])
  }

  @NonCPS
  def removeVotes(changeNumber, label) {
    def changeLabels = query(changeNumber)[0].labels
    if (label in changeLabels) {
      for (reviewer in changeLabels[label].all) {
        if (reviewer.value > 0) {
	  this.removeVote(changeNumber, label, reviewer._account_id)
        }
      }
    }
  }

  // Mark a code review as review started
  @NonCPS
  def startReview(changeNumber) {
    this.addReviewer(changeNumber)
    this.removeVotes(changeNumber, "Presubmit-Ready")
    this.removeVote(changeNumber, "Verified", this.reviewer)
  }

  // Returns the list of verified changes not reviewed by the Gerrit reviewer and matching
  // the given filter. The result is a list of dictionnary of matching change, containing the
  // sha1 of the last patch, the number of this patch, the number of the change, the reference
  // of the patch and the project of the change.
  @NonCPS
  def getVerifiedChanges(filter = "", verifiedLevel = 1, maxChanges = 0) {
    def changesJson = query("status:open ${filter}",
                            maxChanges).findAll { change ->
        def verified = change.labels.get("Presubmit-Ready", [])
        return verified.all.any({ it.value == verifiedLevel })
    }.collect {
      it ->
        def sha1 = it.current_revision
        def patch = it.revisions.get(sha1)
        return [
          "sha1": sha1,
          "number": it._number,
          "patchNumber": patch._number,
          "ref": patch.ref,
          "project": it.project]
    }
    return changesJson
  }
}
