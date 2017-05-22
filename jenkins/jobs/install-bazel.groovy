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

// Install the bazel release on all the machine

import build.bazel.ci.JenkinsUtils

jobs = [:]
nodes = JenkinsUtils.nodeNames("install-bazel")
latest = "latest"

stage("Get latest version of Bazel") {
  latest = installBazel.getLatestBazelVersion()
  echo "Latest bazel version is ${latest}"
}

for (int k = 0; k < nodes.size(); k++) {
  def node = nodes[k]
  if (!node.startsWith("freebsd")) {
    // Skip freebsd who is installed from the port
    jobs[node] = {
      stage("Install Bazel on ${node}") {
        installBazel(node: node,
                     version: latest,
                     flavours: node.startsWith("windows") ? [""] : ["", "-jdk7"],
                     alias: "latest")
      }
    }
  }
}

stage("Install on all nodes") {
  // We fail after 4h in case a node is offline and not comming back online
  timeout(240) {
    parallel jobs
  }
}
