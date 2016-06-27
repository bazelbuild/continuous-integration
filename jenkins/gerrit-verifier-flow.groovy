// Copyright (C) 2015 The Android Open Source Project
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

// Forked from https://gerrit.googlesource.com/gerrit-ci-scripts/+/master/jenkins/gerrit-verifier-flow.groovy

import hudson.model.*
import hudson.AbortException
import hudson.console.HyperlinkNote

import java.util.concurrent.CancellationException
import groovy.json.*
import java.text.*

String.metaClass.encodeURL = {
  java.net.URLEncoder.encode(delegate)
}

class Globals {
  static String gerrit = "https://bazel-review.googlesource.com/"
  static String gerritReviewer = "Bazel CI <ci.bazel@gmail.com>"
  static long curlTimeout = 10000
  static SimpleDateFormat tsFormat = new SimpleDateFormat("YYYY-MM-dd HH:mm:ss.S Z")
  static int maxChanges = 100
  static int myAccountId = 5995
  static int waitForResultTimeout = 10000
  static String cookiesFile = "/opt/secrets/gerritcookies"
  static def gerritJobs = hudson.model.Hudson.instance.items.findAll{job -> job.name.startsWith("Gerrit-")}
}

// Post a JSON payload to the given url setting the correct cookies for authentication.
def gerritPost(url, jsonPayload) {
  def gerritPostUrl = Globals.gerrit + url
  def curl = ['curl', '-n', '-s', '-S',
    "-X", "POST", "-H", "Content-Type: application/json",
    "-b", Globals.cookiesFile,
    "--data-binary", jsonPayload,
    gerritPostUrl ]
  def proc = curl.execute()
  def sout = new StringBuffer(), serr = new StringBuffer()
  proc.consumeProcessOutput(sout, serr)
  proc.waitForOrKill(Globals.curlTimeout)
  def curlExit = proc.exitValue()
  if(curlExit != 0) {
    println "$curl ** FAILED ** with exit code $curlExit"
  }
  if(!serr.toString().trim().isEmpty()) {
    println "--- ERROR ---"
    println serr
  }
  return curlExit
}

// Set a change to verified +1/-1
// Parameters:
//   changeNum: number of the change to mark as verified
//   sha1: SHA-1 sum of the commit to mark as verified
//   verified: +1/-1 value for the verified flag on Gerrit
def gerritReview(changeNum, sha1, verified) {
  if(verified == 0) {
    return;
  }

  def addReviewerExit = gerritPost("a/changes/" + changeNum + "/reviewers", '{ "reviewer" : "' +
                                   Globals.gerritReviewer + '" }')
  if(addReviewerExit != 0) {
    println "**** ERROR: cannot add myself as reviewer of change " + changeNum + " *****"
    return addReviewerExit
  }

  def jsonPayload = '{"labels":{"Code-Review":0,"Verified":' + verified + '},' +
                    ' "notify" : "' + (verified < 0 ? "OWNER":"NONE") + '" }'
  def addVerifiedExit = gerritPost("a/changes/" + changeNum + "/revisions/" + sha1 + "/review",
                                   jsonPayload)

  if(addVerifiedExit == 0) {
    println "----------------------------------------------------------------------------"
    println "Gerrit Review: Verified=" + verified + " to change " + changeNum + "/" + sha1
    println "----------------------------------------------------------------------------"
  }
  return addVerifiedExit
}

// Add a comment without notifying everybody on the change.
//   buildUrl: URL of the build corresponding to that message
//   changeNum: change to comment on
//   sha1: SHA-1 of the commit to comment on
//   msgPrefix: the prefix of the message, the result message will be: <msgPrefix> Bazel CI: <buildUrl>
def gerritComment(buildUrl,changeNum, sha1, msgPrefix) {
  return gerritPost("a/changes/$changeNum/revisions/$sha1/review",
                    "{\"message\": \"$msgPrefix Bazel CI: $buildUrl\", \"notify\" : \"NONE\" }")
}

// Wait for build to finish and return the result of the build.
def waitForResult(build) {
  def result = null
  def startWait = System.currentTimeMillis()
  while(result == null && (System.currentTimeMillis() - startWait) < Globals.waitForResultTimeout) {
    result = build.getResult()
    if(result == null) {
      Thread.sleep(100) {
      }
    }
  }
  return result == null ? Result.FAILURE : result
}

// Convert a build result from Jenkins into a +1/-1/0 for verification bit in Gerrit.
def getVerified(result) {
  if(result == null) {
    return 0;
  }

  switch(result) {
    case Result.SUCCESS:
      return +1;
    case Result.FAILURE:
      return -1;
    default:
      return 0;
  }
}

// Build the jobs associated to a given change.
// This will build all jobs associated to the project the change is submitted to and
// set the verification status: +1 if all build succeed, 0 or -1 if one build
// is interrupted/failed (it stops after the first non successfull build).
def buildChange(change) {
  def sha1 = change.current_revision
  def changeNum = change._number
  def revision = change.revisions.get(sha1)
  def ref = revision.ref
  def patchNum = revision._number
  def branch = change.branch
  def changeUrl = Globals.gerrit + "#/c/" + changeNum + "/" + patchNum
  def refspec = "+" + ref + ":" + ref.replaceAll('ref/', 'ref/remotes/origin/')
  def jobs = Globals.gerritJobs.findAll{job -> job.description.contains("Gerrit project: " + change.project + ".\n")}

  if (!jobs.empty) {
    println "Building Change " + changeUrl
    def result = null
    for (job in jobs) {
      def b = build(job.name, REFSPEC: refspec, BRANCH: sha1, CHANGE_URL: changeUrl)
      result = waitForResult(b)
      gerritComment(b.getBuildUrl(), change._number, change.current_revision,
                    "Build for job " + job.name + " finished with status " + result + " on ")
      if (result != Result.SUCCESS) {
        break;
      }
    }
    gerritReview(changeNum,sha1,getVerified(result))
  } else {
    gerritComment(build.startJob.getBuildUrl() + "console",change._number,change.current_revision,"Verification skipped (no job) by ")
  }
}

// The main loop

// Get information from the last build
def lastBuild = build.getPreviousBuild()
def logOut = new ByteArrayOutputStream()

if(lastBuild != null) {
  lastBuild.getLogText().writeLogTo(0,logOut)
}

def lastLog = new String(logOut.toByteArray())
def lastBuildStartTimeMillis = lastBuild == null ?
  (System.currentTimeMillis() - 1800000) : lastBuild.getStartTimeInMillis()
def sinceMillis = lastBuildStartTimeMillis - 30000
def since = Globals.tsFormat.format(new Date(sinceMillis))

if(lastBuild != null) {
  println "Last build was " + lastBuild.toString()
}

// Get open gerrit changes
def gerritQuery = "status:open since:\"" + since + "\""

def requestedChangeId = params.get("CHANGE_ID")
def processAll = requestedChangeId.equals("ALL")

queryUrl = processAll ?
    new URL(Globals.gerrit + "changes/?pp=0&o=DETAILED_LABELS&o=CURRENT_REVISION&n=" + Globals.maxChanges + "&q=" + gerritQuery.encodeURL()) :
    new URL(Globals.gerrit + "changes/?pp=0&o=DETAILED_LABELS&o=CURRENT_REVISION&q=" + requestedChangeId)
def changes = queryUrl.getText().substring(5)
def jsonSlurper = new JsonSlurper()
def changesJson = jsonSlurper.parseText(changes)


// Accept change that have been marked verified and not yet processed
def acceptedChanges = changesJson.findAll {
  change ->
  sha1 = change.current_revision
  if(processAll && lastLog.contains(sha1)
        && !lastLog.contains("Nobody has approved commit " + sha1)) {
      println "Skipping SHA1 " + sha1 + " because has been already built by " + lastBuild
      return false
  }

  def verified = change.labels.Verified
  if (verified != null) {
    // This one has the verified label, let's try to test it
    def approved = verified.all.findAll({x -> x.value == 1}).collect({x -> x._account_id})
    def rejected = verified.all.findAll({x -> x.value == -1}).collect({x -> x._account_id})

    if (processAll && approved && Globals.myAccountId in approved) {
      println "I have already approved commit " + sha1 + " of change " + change._number + ": SKIPPING"
      return false
    } else if (processAll && rejected && Globals.myAccountId in rejected) {
      println "I have already rejected commit " + sha1 + " of change " + change._number + ": SKIPPING"
      return false
    } else if (!approved) {
      println "Nobody has approved commit " + sha1 + " of change " + change._number + ": SKIPPING"
      return false
    } else {
      gerritComment(build.startJob.getBuildUrl() + "console",change._number,change.current_revision,"Verification queued on")
      return true
    }
  }
}

println "Gerrit has " + acceptedChanges.size() + " change(s) since " + since
println "================================================================================"

// And finally build accepted changes
for (change in acceptedChanges) {
  buildChange(change)
}
