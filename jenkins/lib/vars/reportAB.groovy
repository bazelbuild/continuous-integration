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

// Step to report failure of a set of jobs and comparing the result with
// the latest jobs with the same name on another folder
import build.bazel.ci.JenkinsUtils

@NonCPS
def formatRun(run) {
  if (run == null) {
    return "unkown status"
  }
  def console = JenkinsUtils.getConsoleUrl(run)
  def url = JenkinsUtils.getBlueOceanUrl(run)
  def icon = JenkinsUtils.getSmallIconUrl(run)
  return "<a href=\"${console}\"><img src=\"${icon}\"/></a> <a href=\"${url}\">#${run.number}</a>"
}

@NonCPS
def collectJobs(report, beforeFolder) {
  def successes = []
  def failures = []
  def alreadyFailing = []
  for (e in report) {
    def key = e.key
    def value = e.value
    def beforeJob = JenkinsUtils.getLastRun(beforeFolder, key)
    def element = "${key} ${formatRun(value)} (was ${formatRun(beforeJob)})"
    if (value.result == "SUCCESS") {
      successes <<= element
    } else if (beforeJob == null || beforeJob.rawBuild.result.isWorseOrEqualTo(value.rawBuild.result)) {
      alreadyFailing <<= element
    } else {
      failures <<= element
    }
  }
  return [failures: failures, alreadyFailing: alreadyFailing, successes: successes]
}

@NonCPS
def toHTMLList(lst) {
  def listItems = lst.collect { "<li>${it}</li>" }
  return "<ul>${listItems.join('\n')}</ul>"
}

def call(args = [:]) {
  def name = args.name
  def jobs = collectJobs(args.report, args.get("beforeFolder", ""))
  node {
    writeFile file: (".report/${name}.html"), text: """
<html>
<h2>Newly failing jobs</h2>
<ul>${toHTMLList(jobs.failures)}</ul>
<h2>Already failing jobs</h2>
<ul>${toHTMLList(jobs.alreadyFailing)}</ul>
<h2>Passing jobs</h2>
<ul>${toHTMLList(jobs.successes)}</ul>
</html>
"""
    publishHTML target: [
      allowMissing: false,
      alwaysLinkToLastBuild: false,
      keepAll: true,
      reportDir: ".report",
      reportFiles: "${name}.html",
      reportName: name
    ]
  }

  if (args.get("unstableOnNewFailure", true) && !jobs.failures.empty) {
    currentBuild.result = "UNSTABLE"
  }
}
