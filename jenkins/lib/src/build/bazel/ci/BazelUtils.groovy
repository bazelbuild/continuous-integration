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

import groovy.json.JsonSlurper

/**
 * A set of utility methods to call Bazel inside Jenkins
 */
class BazelUtils implements Serializable {
  private static final TEST_EVENTS_FILE = "bazel-events-test.json"
  private static final BUILD_EVENTS_FILE = "bazel-events-build.json"
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

  // Actual method

  private def execute(script, returnStatus = false, returnStdout = false) {
    if (isWindows) {
      if (returnStdout) {
        // @ removes the command lines from the output
        script = "@${script}"
      }
      // exit /b !ERRORLEVEL! actually returns the exit code
      return this.script.bat(script: "${script}\r\n@exit /b %ERRORLEVEL%",
                             returnStatus: returnStatus, returnStdout: returnStdout)
    } else {
      return this.script.sh(script: script, returnStatus: returnStatus, returnStdout: returnStdout)
    }
  }

  def bazelCommand(String args, returnStatus = false, returnStdout = false) {
    script.withEnv(envs + ["BAZEL=" + this.bazel]) {
      owner.script.ansiColor("xterm") {
        return execute("${this.bazel} --bazelrc=${this.ws}/bazel.bazelrc ${args}",
                       returnStatus, returnStdout)
      }
    }
  }


  // Write a RC file to consume by the other step
  def writeRc(build_opts = [],
              test_opts = [],
              extra_bazelrc = "") {
    def rc_file_content = [
      "common --color=yes",
      "test --test_output=errors",
      "build --verbose_failures"
    ]
    rc_file_content.addAll(build_opts.collect { "build ${it}" })
    rc_file_content.addAll(test_opts.collect { "test ${it}" })
    for(opt in build_opts) {
      rc_file_content += "\nbuild ${opt}"
    }
    for(opt in test_opts) {
      rc_file_content += "\ntest ${opt}"
    }
    // Store the BEP events on a json file.
    // TODO(dmarting): We should archive it and generate a good HTML report instead of
    // the hard to read jenkins dashboard.
    rc_file_content.add("build --experimental_build_event_json_file=${BUILD_EVENTS_FILE}")
    rc_file_content.add("test --experimental_build_event_json_file=${TEST_EVENTS_FILE}")
    script.writeFile(file: "${ws}/bazel.bazelrc",
                     text: rc_file_content.join("\n") + "\n${extra_bazelrc}")
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
      def filteredTests = bazelCommand("query \"tests(${tests.join ' + '})\"", false, true)
      if (filteredTests.isEmpty()) {
        script.echo "Skipped tests (no tests found)"
      } else {
        def status = bazelCommand("test ${filteredTests.replaceAll("\n", " ")}", true)
        if (status == 3) {
          // Bazel returns 3 if there was a test failures but no breakage, that is unstable
          script.currentBuild.result = "UNSTABLE"
        } else if (status != 0) {
          // TODO(dmarting): capturing the output mark the wrong step at failure, there is
          // no good way to do so, it would probably better to have better output in the failing
          // step
          script.error("`bazel test` returned status ${status}")
        }
      }
    }
  }

  private def parseEventsFile(String fileName) {
    // We requires that weirdness because the format of the events are not one JSON object
    // but a sequence of JSON Object.
    if (script.fileExists(fileName)) {
      def content = script.readFile(fileName).replaceAll('\n}(?!\\s*$)', '\n},')
      return new JsonSlurper().parseText("[${content}]")
    }
    // The file does not exists (probably because empty set of targets / tests), just return
    // an empty list.
    return []
  }

  def buildEvents() {
    return parseEventsFile("${this.ws}/${BUILD_EVENTS_FILE}")
  }

  def testEvents() {
    return parseEventsFile("${this.ws}/${TEST_EVENTS_FILE}")
  }

  @NonCPS
  def generateTestLogsCopy(events, test_folder) {
    // To avoid looking at all the files, including the stalled output log, we parse the events
    // from the build.
    // This is NonCPS because lambdas
    def cp_lines = []
    events.each { event ->
      if("testResult" in event) {
        def uri = URI.create(event.testResult.testActionOutput.find { it.name == "test.xml" }.uri)
        def relativePath = uri.path.substring(uri.path.indexOf("/testlogs/") + 10)
        cp_lines.add("mkdir -p \$(dirname '${test_folder}/${relativePath}')")
        cp_lines.add("cp -r '${uri.path}' '${test_folder}/${relativePath}'")
      }
    }
    return cp_lines.join('\n')
  }

  // Archive test results
  def testlogs(test_folder) {
    // JUnit test result does not look at test result if they are "old", copying them to a new
    // location, unique accross configurations.
    def res = script.sh(
      script: "rm -fr ${test_folder}\n" + generateTestLogsCopy(testEvents(), test_folder),
      returnStatus: true)
    if (res == 0) {
      script.junit testResults: "${test_folder}/**/test.xml", allowEmptyResults: true
    }
  }
}
