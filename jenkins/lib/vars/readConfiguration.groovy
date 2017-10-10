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

import build.bazel.ci.BazelConfiguration

// Step to read a configuration from the repository
// Parameters:
//   - repository, branch, refspec: which repository to fetch, see recursiveGit
//   - files: the list of files to read from the repository (if the first one
//     does not exists, try the second one and so on...), default to .ci/bazel.json.
//   - default_configuration: default json content to use if the file cannot be found
//   - restrict_configuration: restriction to the returned configuration, see
//     BazelConfiguration.flattenConfiguration
def call(config = [:]) {
  def conf = null
  def files = config.get("files", [".ci/bazel.json"])
  def filename = null
  if ("repository" in config) {
    node {
      recursiveGit(repository: config.repository,
                   branch: config.get("branch", "master"),
                   refspec: config.get("refspec", "+refs/heads/*:refs/remotes/origin/*"))
      for(int k = 0; k < files.size() && conf == null; k++) {
        if (fileExists(files[k])) {
          filename = files[k]
          conf = readFile(filename)
        }
      }
    }
  }
  if (conf == null) {
    conf = config.get("default_configuration")
    if (conf == null) {
      error(
        """Cannot read configuration file from the repository and no fallback was provided.
Please check a configuration file under one of: ${files.join ', '}.""")
    }
  }
  try {
    // We exclude the deploy slaves from being selected by the configuration, they
    // have access to secrets.
    return BazelConfiguration.flattenConfigurations(
      BazelConfiguration.parse(conf), config.get("restrict_configuration", [:]),
      ["node": ["deploy", "deploy-staging"]])
  } catch(Exception ex) {
    error(filename != null ? "Failed to validate configuration (file was ${filename}): ${ex.message}"
          : "Failed to validate default configuration: ${ex.message}")
  }
}
