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
package build.bazel.ci.utils

import org.junit.Before
import com.lesfurets.jenkins.unit.BasePipelineTest
import com.lesfurets.jenkins.unit.global.lib.LibraryConfiguration

// A base class for all test testing the library as a whole using PipelineUnitTest
abstract class BaseLibraryTest extends BasePipelineTest {

  @Override
  @Before
  void setUp() throws Exception {
    def library = LibraryConfiguration.library()
                .name('opt-lib')
                .retriever(new FsSource("${System.getenv('TEST_SRCDIR')}/io_bazel_ci/jenkins/lib"))
                .targetPath("does/not/matter")
                .implicit(true)
                .defaultVersion("master")
                .build()
    helper.registerSharedLibrary(library)
    registerAllowedMethods()
    super.setUp()
  }

  void registerAllowedMethods() {
    // TODO(dmarting): these are dumnies, we probably want to control that more
    // to test all codepaths.
    helper.registerAllowedMethod("pwd", [], { -> "/some/path"})
    helper.registerAllowedMethod("isUnix", [], { -> true})
    helper.registerAllowedMethod("file", [Map.class], { m ->
      def fileContent = "/path/to/${m.credentialsId})"
      binding.setVariable(m['variable'], fileContent)
      return fileContent
    })
    helper.registerAllowedMethod("writeFile", [Map.class], { m -> })
    helper.registerAllowedMethod("withEnv", [List.class, Closure.class], { l, c -> c() })
    helper.registerAllowedMethod("ansiColor", [String.class, Closure.class], { l, c -> c() })
    helper.registerAllowedMethod("fileExists", [String.class], { f -> false })
  }

  def mktemp(fileName) {
    def tempDir = new File(System.getenv("TEST_TMPDIR"))
    def counter = 0
    while (new File(tempDir, "${counter}${fileName}").exists()) {
      counter++
    }
    return new File(tempDir, "${counter}${fileName}")
  }

  def evalScript(String script) {
    def tempFile = mktemp("script.groovy")
    try {
      tempFile.write script
      loadScript(tempFile.path)
    } finally {
      tempFile.delete()
    }
  }
}
