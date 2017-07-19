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

// Step to run all job matching certain criterium
import build.bazel.ci.JenkinsUtils

def call(params = [:]) {
  def folder = params.get("folder", null)
  def excludes = params.get("excludes", [currentBuild.getProjectName()])
  def parameters = params.get("parameters", [])
  def wait = params.get("wait", true)
  def catchError = params.get("catchError", false)
  def statusOnError = params.get("statusOnError", "FAILURE")
  def statusOnFailure = params.get("statusOnFailure", "SUCCESS")
  def statusOnUnstable = params.get("statusOnUnstable", "SUCCESS")
  def jobs = JenkinsUtils.jobs(folder).toArray()
  def toRun = [:]
  def report = [:]
  for (int k = 0; k < jobs.length; k++) {
    def jobName = jobs[k]
    if (!(jobName in excludes)) {
      toRun[jobName] = { ->
        try {
          r = build(job: folder ? "/${folder}/${jobName}" : jobName,
                    parameters: parameters,
                    wait: wait,
                    propagate: false)
          if (r.result == "FAILURE") {
            currentBuild.result = statusOnFailure
          } else if (r.result == "UNSTABLE") {
            currentBuild.result = statusOnUnstable
          }
          report.put(jobName, r)
        } catch(error) {
          if (catchError) {
            echo "Catched ${error} from upstream job ${jobName}"
            currentBuild.result = statusOnError
          } else {
            throw error
          }
        }
      }
    }
  }
  jobs = null
  parallel(toRun)

  return report
}
