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

import org.junit.Test

/** Tests for {@link BazelConguration} */
class BazelConfigurationTests {
  static final String JSON_TEST = '''

// This is a test
// Double comment to test the workaround the parser issue

// more comment
// And now the initial bazel tests
[
    {
        // This is a configuration that have 3 subconfiguration: linux, ubuntu and darwin
        // Each of those configuration have 4 bazel variations: HEAD, HEAD-jdk7, latest,
        // and latest-jdk7
        "configurations": [
            {
                "node": "linux-x86_64",
                "configurations": [
                    // XXX(dmarting): Remove HEAD from here.
                    {"variation": "HEAD"},
                    {"variation": "HEAD-jdk7"},
                    {"variation": "latest"},
                    {"variation": "latest-jdk7"}
                ]
            },
            {
                "node": "ubuntu_16.04-x86_64",
                "configurations": [
                    {"variation": "HEAD"},
                    {"variation": "HEAD-jdk7"},
                    {"variation": "latest"},
                    {"variation": "latest-jdk7"}
                ]
            },
            {
                "node": "darwin-x86_64",
                "configurations": [
                    {"variation": "HEAD"},
                    {"variation": "HEAD-jdk7"},
                    {"variation": "latest"},
                    {"variation": "latest-jdk7"}
                ]
            }
        ],
        // And specify the parameters for these configurations.
        "parameters": {
            "configure": [
                "source scripts/ci/build.sh",
                "setup_android_repositories"
            ],
            "test_opts": ["-k", "--build_tests_only"],
            "tests": [
                "//scripts/...",
                "//src/...",
                "//third_party/ijar/..."
            ],
            "targets": []
        }
    }, {
        "toolchain": "msvc",
        "configurations": [{
            // XXX(dmarting): MSVC is a misnommer, it should have been called win32
            // (for win32 native binary).
            // XXX(dmarting): really MSVC/Win32 should be a bazel variation, not part of
            // the node.
            "node": "windows-msvc-x86_64",
            "configurations": [{"variation": "HEAD"},{"variation": "latest"}]
        }, {
            "node": "windows-x86_64",
            "configurations": [{"variation": "HEAD"},{"variation": "latest"}]
        }],
        "parameters": {
            "test_opts": ["-k", "--build_tests_only"],
            "tests": [
                "//src/test/java/...",
                "//src/test/cpp/...",
                "//src/test/naive:all_tests"
            ],
            "targets": ["//src:bazel"]
        }
    }, {
        "toolchain": "msys",
        "configurations": [{
            "node": "windows-msvc-x86_64",
            "configurations": [{"variation": "HEAD"},{"variation": "latest"}]
        }, {
            "node": "windows-x86_64",
            "configurations": [{"variation": "HEAD"},{"variation": "latest"}]
        }],
        "parameters": {
            "test_opts": ["-k", "--build_tests_only"],
            "tests": ["//src/tst/shell/bazel:bazel_windows_example_test"],
            "targets": []
        }
    }
]

// Ending comment
'''

  private void assertConfigurationCorrect(confs) {
    assert confs.size() == 3
    assert confs[0].descriptor.size() == 0
    assert confs[0].parameters.size() == 4
    assert confs[0].parameters["configure"] == [
      "source scripts/ci/build.sh",
      "setup_android_repositories"
    ]
    assert confs[0].configurations.size() == 3
    assert confs[0].configurations.every {
      v -> v.configurations.size() == 4 && v.parameters.size() == 0 && v.descriptor.size() == 1 }
    assert confs[1].descriptor.size() == 1
    assert confs[1].parameters.size() == 3
    assert confs[1].configurations.size() == 2
    assert confs[1].configurations.every {
      v -> v.configurations.size() == 2 && v.parameters.size() == 0 && v.descriptor.size() == 1 }
    assert confs[2].descriptor.size() == 1
    assert confs[2].parameters.size() == 3
    assert confs[2].configurations.size() == 2
    assert confs[2].configurations.every {
      v -> v.configurations.size() == 2 && v.parameters.size() == 0 && v.descriptor.size() == 1 }
  }

  @Test
  void testParseJsonString() {
    assertConfigurationCorrect(BazelConfiguration.parse(JSON_TEST))
  }

  @Test
  void testSerialization() {
    // Just test that the object from parsing JSON is serializable
    new ObjectOutputStream(new ByteArrayOutputStream()).writeObject(BazelConfiguration.parse(JSON_TEST));
  }

  @Test
  void testParseJsonFile() {
    def tempDir = System.getenv("TEST_TMPDIR")
    def tempDirFile = null
    if (tempDir != null) {
      tempDirFile = new File(tempDir)
    }
    def testFile = File.createTempFile('temp', '.json', tempDirFile)
    try {
      testFile.write(JSON_TEST)
      assertConfigurationCorrect(BazelConfiguration.parse(testFile))
    } finally {
      testFile.delete()
    }
  }

  @Test
  void testFlatten() {
    def result = BazelConfiguration.flattenConfigurations(BazelConfiguration.parse(JSON_TEST))
    def allKeys = result.collect {
      k, v -> k.collect { k1, v1 -> "${k1}=${v1}" }.toSorted().join(",") }.toSorted()
    // Once flatten there are 20 configurations
    assert allKeys.size() == 20
    assert allKeys.join("\n") == '''node=darwin-x86_64,variation=HEAD
node=darwin-x86_64,variation=HEAD-jdk7
node=darwin-x86_64,variation=latest
node=darwin-x86_64,variation=latest-jdk7
node=linux-x86_64,variation=HEAD
node=linux-x86_64,variation=HEAD-jdk7
node=linux-x86_64,variation=latest
node=linux-x86_64,variation=latest-jdk7
node=ubuntu_16.04-x86_64,variation=HEAD
node=ubuntu_16.04-x86_64,variation=HEAD-jdk7
node=ubuntu_16.04-x86_64,variation=latest
node=ubuntu_16.04-x86_64,variation=latest-jdk7
node=windows-msvc-x86_64,toolchain=msvc,variation=HEAD
node=windows-msvc-x86_64,toolchain=msvc,variation=latest
node=windows-msvc-x86_64,toolchain=msys,variation=HEAD
node=windows-msvc-x86_64,toolchain=msys,variation=latest
node=windows-x86_64,toolchain=msvc,variation=HEAD
node=windows-x86_64,toolchain=msvc,variation=latest
node=windows-x86_64,toolchain=msys,variation=HEAD
node=windows-x86_64,toolchain=msys,variation=latest'''
  }

  @Test
  void testFlattenWithRestriction() {
    def result = BazelConfiguration.flattenConfigurations(
      BazelConfiguration.parse(JSON_TEST),
      [node: ["linux-x86_64", "windows-x86_64"], variation: ["HEAD", "HEAD-jdk7"]])
    def allKeys = result.collect {
      k, v -> k.collect { k1, v1 -> "${k1}=${v1}" }.toSorted().join(",") }.toSorted()
    assert allKeys.size() == 4
    assert allKeys.join("\n") == '''node=linux-x86_64,variation=HEAD
node=linux-x86_64,variation=HEAD-jdk7
node=windows-x86_64,toolchain=msvc,variation=HEAD
node=windows-x86_64,toolchain=msys,variation=HEAD'''
  }
}
