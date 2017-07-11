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

/** Tests for {@link JsonUtils} */
class JsonUtilsTests {

  private static assertJsonResult(result) {
    assert result.size() == 2
    assert result[0].size() == 1
    assert "a" in result[0]
    assert "b" in result[0].a
    assert "c".equals(result[0].a.b)
    assert result[1].size() == 1
    assert "c" in result[1]
    assert "d" in result[1].c
    assert "e".equals(result[1].c.d)
  }

  @Test
  void testParseJsonStreamOneLine() {
    assertJsonResult(JsonUtils.parseJsonStream('{"a": {"b":"c"}}{"c": {"d":"e"}}'))
  }

  @Test
  void testParseJsonStreamMultiLine() {
    assertJsonResult(JsonUtils.parseJsonStream('{"a": {"b":"c"}}\n{"c": {"d":"e"}}\n'))
  }

  @Test
  void testParseJsonStreamMultiMultiLine() {
    assertJsonResult(JsonUtils.parseJsonStream('{"a": \n{\n"b":"c"\n}\n}\n{\n"c": \n{\n"d":"e"\n}\n}\n'))
  }

  @Test
  void testParseTimestampLike() {
    // Just test we do not raise an error
    JsonUtils.parseJsonStream('{"a": "static const char kTimestampFormat[] = \\"%E4Y-%m-%dT%H:%M:%S\\";"}')
  }

  @Test
  void testSerializable() {
    // Try to serialize the output
    def m = JsonUtils.parseJsonStream('{"a": \n{\n"b":"c"\n}\n}\n{\n"c": \n{\n"d":"e"\n}\n}\n')
    def ostream = new PipedOutputStream()
    def istream = new PipedInputStream(ostream)
    new ObjectOutputStream(ostream).writeObject(m)
    new ObjectInputStream(istream).readObject()
  }
}
