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

import com.cloudbees.groovy.cps.NonCPS
import groovy.json.JsonSlurperClassic

/**
 * A set of utility methods to handle JSON format emitted by Bazel.
 * This is a separate class to be able to test it without pulling in a lot
 * of dependency.
 */
class JsonUtils {

  @NonCPS
  private static def tokenToText(token) {
    if (token.getType() == groovy.json.JsonTokenType.STRING) {
      return groovy.json.JsonOutput.toJson(token.value)
    } else {
      return token.text
    }
  }

  @NonCPS
  public static def parseJsonStream(String stream) {
    // We require that weirdness because the format of the events are not one JSON object
    // but a sequence of JSON Object. Note that even hacking an input stream and iterating
    // over is not enough because JsonSlurper seems like to consume all the stream even
    // though it returns only the first element.
    def lexer = new groovy.json.JsonLexer(new StringReader(stream))
    def parser = new JsonSlurperClassic()
    def res = []
    def builder = new StringBuffer()
    def counter = 0
    while (lexer.hasNext()) {
      def tok = lexer.next()
      if (tok.getType() == groovy.json.JsonTokenType.OPEN_CURLY) {
        counter++;
        builder.append("{")
      } else if (tok.getType() == groovy.json.JsonTokenType.CLOSE_CURLY) {
        counter--;
        if (counter == 0) {
          res <<= parser.parseText(builder.toString() + "}")
          builder.setLength(0)
        } else {
          builder.append("}")
        }
      } else {
        builder.append(tokenToText(tok))
      }
    }
    // We might have trailing tokens, just ignore them as they would mean
    // an incomplete file.
    // TODO(dmarting): we should probably print a warning here.
    return res
  }
}
