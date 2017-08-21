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

// This is the one pipeline to rule them all
import build.bazel.ci.BazelUtils
import java.util.concurrent.TimeUnit

def newChanges = false
def filename = "output/build_${currentBuild.getId()}.json"

timeout(time: 20, unit: TimeUnit.HOURS) {
  node("benchmark") {
    stage("Clone") {
      recursiveGit(repository: "https://bazel.googlesource.com/bazel",
                   branch: "master")
    }

    // Build the benchmark binary
    def utils = new BazelUtils()
    utils.bazel = bazelPath("latest", "linux-x86_64")
    utils.script = this
    utils.writeRc()
    stage("Building benchmark") {
      utils.build(["//src/tools/benchmark/java/com/google/devtools/build/benchmark"])
    }

    // Run the benchmark
    stage("Running benchmark") {
      def workspace = pwd()
      // Get only version from Bazel, not from the Jenkins lib.
      // Unfortunately we do not have the origin information so we filter out
      // commit by "nobody".
      def versions = []
      for (def lst : currentBuild.getChangeSets()) {
        for (def item : lst) {
          if (!item.author.toString().equals("nobody")) {
            versions <<= "--versions=${item.commitId}"
          }
        }
      }
      if (versions.isEmpty()) {
        echo "No new changes, skipping"
      } else {
        newChanges = true
        def args = [
          "bazel-bin/src/tools/benchmark/java/com/google/devtools/build/benchmark/benchmark",
          "--workspace=${workspace}/benchmark_workspace",
          "--output=${workspace}/${filename}"] + versions
        dir("output") { writeFile file:"dummy", text: "" }
        utils.commandWithBazelOnPath(args.join(" "))
        stash name:"benchmark-results", includes:filename
      }
    }
  }
}

stage("Deploying benchmark results") {
  if (newChanges) {
    node("deploy") {
      // TODO(dmarting): since we are moving deployment of website we should
      // also move the deployment of benchmark out of bazel.
      recursiveGit(repository: "https://bazel.googlesource.com/bazel",
                   branch: "master")
      unstash "benchmark-results"
      sh """
bash -c 'source scripts/ci/build.sh; push_benchmark_output_to_site ${filename} perf.bazel.build'
"""
    }
  }
}
