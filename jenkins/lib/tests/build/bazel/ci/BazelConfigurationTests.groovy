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

  // The contents of this JSON string don't matter, i.e. it doesn't have to
  // refer to existing target patterns for example.
  // The test only asserts the structure of the JSON.
  static final String JSON_TEST = '''

// This is a test
// Double comment to test the workaround the parser issue

// more comment
// And now the initial bazel tests
[
    {
        // This is a configuration that have 3 subconfiguration: linux, ubuntu and darwin
        "configurations": [
            {
                "node": "linux-x86_64"
            },
            {
                "node": "ubuntu_16.04-x86_64"
            },
            {
                "node": "darwin-x86_64"
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
                "//dummy_path1/...",
                "//dummy_path2/...",
                "//dummy/path3/..."
            ],
            "targets": []
        }
    }, {
        "configurations": [{
            "node": "windows-x86_64",
        }],
        "parameters": {
            "test_opts": ["-k", "--build_tests_only"],
            "tests": [
                "//some/dummy/java_test/...",
                "//some/dummy/cpp_test/...",
                "//some/dummy/native_test:all_tests"
            ],
            "targets": ["//src:bazel"]
        }
    }
]

// Ending comment
'''

  private void assertConfigurationCorrect(confs) {
    assert confs.size() == 2
    assert confs[0].parameters.size() == 4
    assert confs[0].parameters["configure"] == [
      "source scripts/ci/build.sh",
      "setup_android_repositories"
    ]
    assert confs[0].configurations.size() == 3
    assert confs[1].parameters.size() == 3
    assert confs[1].configurations.size() == 1
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
    assert allKeys.join("\n") == '''node=darwin-x86_64
node=linux-x86_64
node=ubuntu_16.04-x86_64
node=windows-x86_64'''
  }

  @Test
  void testFlattenWithRestriction() {
    def result = BazelConfiguration.flattenConfigurations(
      BazelConfiguration.parse(JSON_TEST),
      [node: ["linux-x86_64", "windows-x86_64"]])
    def allKeys = result.collect {
      k, v -> k.collect { k1, v1 -> "${k1}=${v1}" }.toSorted().join(",") }.toSorted()
    assert allKeys.join("\n") == '''node=linux-x86_64
node=windows-x86_64'''
  }

  @Test
  void testFlattenWithRestrictionNoWindows() {
    def result = BazelConfiguration.flattenConfigurations(
      BazelConfiguration.parse(JSON_TEST),
      [node: ["linux-x86_64"]])
    def allKeys = result.collect {
      k, v -> k.collect { k1, v1 -> "${k1}=${v1}" }.toSorted().join(",") }.toSorted()
    assert allKeys.join("\n") == '''node=linux-x86_64'''
  }

  @Test
  void testFlattenWithExclusion() {
    def result = BazelConfiguration.flattenConfigurations(
      BazelConfiguration.parse(JSON_TEST), [:],
      [node: ["ubuntu_16.04-x86_64", "darwin-x86_64"]])
    def allKeys = result.collect {
      k, v -> k.collect { k1, v1 -> "${k1}=${v1}" }.toSorted().join(",") }.toSorted()
    assert allKeys.join("\n") == '''node=linux-x86_64
node=windows-x86_64'''
  }
}
