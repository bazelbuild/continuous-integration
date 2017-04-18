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

package build.bazel.ci

/**
 * A set of utility methods to call Bazel inside Jenkins
 */
class BazelUtils implements Serializable {
  private String bazel;
  private String ws;
  private def script;
  private boolean isWindows;
  private def envs = [];

  // Accessors
  def setBazel(value) {
    bazel = value
  }
  def getBazel() {
    bazel
  }
  def setScript(value) {
    script = value
    ws = script.pwd()
    isWindows = !script.isUnix()
    if (isWindows) {
      def bazel_sh = script.sh(script: "cygpath --windows /bin/bash",
                               returnStdout: true).trim()
      envs = ["BAZEL_SH=${bazel_sh}"]
    }
  }
  def getScript() {
    script
  }

  private def execute(script, returnStatus = false, returnStdout = false) {
    if (isWindows) {
      return this.script.bat(script: script, returnStatus: returnStatus, returnStdout: returnStdout)
    } else {
      return this.script.sh(script: script, returnStatus: returnStatus, returnStdout: returnStdout)
    }
  }

  def bazelCommand(String args, returnStatus = false, returnStdout = false) {
    script.withEnv(envs + ["BAZEL=" + this.bazel]) {
      owner.script.ansiColor("xterm") {
        return execute("${this.bazel} --bazelrc=${this.ws}/bazel.bazelrc --nomaster_bazelrc ${args}",
                       returnStatus, returnStdout)
      }
    }
  }

  // Actual method

  // Write a RC file to consume by the other step
  def writeRc(build_opts = [],
              test_opts = [],
              extra_bazelrc = "") {
    def rc_file_content = "common --color=yes\ntest --test_output=errors\nbuild --verbose_failures"
    for(opt in build_opts) {
      rc_file_content += "\nbuild ${opt}"
    }
    for(opt in test_opts) {
      rc_file_content += "\ntest ${opt}"
    }
    script.writeFile file: "${ws}/bazel.bazelrc", text: rc_file_content + "\n${extra_bazelrc}"
  }

  // Execute a bazel build
  def build(targets = ["//..."]) {
    if (!targets.isEmpty()) {
      bazelCommand("build ${targets.join ' '}")
    }
  }

  // Execute a bazel tests
  def test(tests = ["//..."]) {
    if (!tests.isEmpty()) {
      def filteredTests = bazelCommand("query 'tests(${tests.join ' + '})'", false, true)
      def status = bazelCommand("test ${filteredTests.replaceAll("\n", " ")}", true)
      if (status == 3) {
        // Bazel returns 3 if there was a test failures but no breakage, that is unstable
        script.currentBuild.result = "UNSTABLE"
      } else if (status != 0) {
        script.currentBuild.result = "FAILURE"
        // TODO(dmarting): capturing the output mark the wrong step at failure, there is
        // no good way to do so, it would probably better to have better output in the failing
        // step
        script.error("`bazel test` returned status ${status}")
      }
    }
  }

  // Archive test results
  def testlogs(test_folder) {
    // JUnit test result does not look at test result if they are "old", copying them to a new
    // location, unique accross configurations.
    def res = script.sh(
      script: "rm -fr ${test_folder}; mkdir -p ${test_folder}; cp -r bazel-testlogs/* ${test_folder}",
      returnStatus: true)
    if (res == 0) {
      script.junit testResults: "${test_folder}/**/test.xml", allowEmptyResults: true
    }
  }
}
