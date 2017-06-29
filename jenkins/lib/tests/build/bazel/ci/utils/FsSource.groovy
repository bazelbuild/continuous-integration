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

// An implementation of SourceRetriever that simply reads a directory
// LocalSource expect a sub-directory 'repository@branch', so we cannot use it.
package build.bazel.ci.utils

import com.lesfurets.jenkins.unit.global.lib.SourceRetriever
import javax.annotation.concurrent.Immutable
import groovy.transform.CompileStatic

@Immutable
@CompileStatic
class FsSource implements SourceRetriever {
  private final String directory

  public FsSource(String directory) {
    this.directory = directory;
  }

  @Override
  List<URL> retrieve(String repository, String branch, String targetPath) {
    def sourceDir = new File(directory)
    if (sourceDir.exists()) {
      return [sourceDir.toURI().toURL()]
    }
    throw new IllegalStateException("Directory ${directory} does not exists")
  }

  @Override
  String toString() {
    return "FsSource{directory='${directory}'}"
  }
}
