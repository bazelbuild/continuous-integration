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
  def jobs = JenkinsUtils.jobs(folder).toArray()
  def toRun = [:]
  def report = [:]
  for (int k = 0; k < jobs.length; k++) {
    def jobName = jobs[k]
    if (!(jobName in excludes)) {
      toRun[jobName] = { ->
          r = build(job: folder ? "/${folder}/${jobName}" : jobName,
                    parameters: parameters,
                    wait: wait,
                    propagate: false)
          report.put(jobName, r)
	  echo "Details of ${jobName}: ${JenkinsUtils.getBlueOceanUrl(r)}"
          if (r.result == "FAILURE" || r.result == "UNSTABLE"
	      || r.result == "ABORTED") {
            throw new Exception("Failed on " + jobName + ": " + r.result);
          }
        }
    }
  }
  jobs = null
  try {
    parallel(toRun)
  } catch(Exception e) {
    // back to normal execution, to have the report available
  }

  return report
}
