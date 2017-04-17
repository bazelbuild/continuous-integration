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

import groovy.io.FileType
import org.junit.Test

/** Test that assert that all json files in the runfiles can be parsed with {@link BazelConguration} */
class BazelConfigurationParsingTest {
  private def findJSONFiles(File baseDir) {
    def result = []
    baseDir.eachFileRecurse(FileType.FILES) {
      if(it.name.endsWith('.json')) {
        result.add(it)
      }
    }
    return result
  }

  @Test
  void testParse() {
    def runfileDir = System.getenv("JAVA_RUNFILES")
    for (File f : findJSONFiles(new File(runfileDir))) {
      // Just test that parsing succeed to ensure that we can at least load the
      // file on Jenkins.
      BazelConfiguration.parse(f)
    }
  }
}
