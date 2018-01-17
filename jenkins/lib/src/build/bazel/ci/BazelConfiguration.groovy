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
import groovy.json.JsonSlurper
import groovy.json.JsonParserType

/**
 * A class that stores configuration for a Bazel job.
 *
 * A configuration is composed of a descriptor and a list of parameters.
 * A descriptor is a key-value map describing the configuration itself and
 * parameters are parameters for the job common to all configurations but for
 * which the value is configuration specific. E.g. test options or targets to
 * build.
 *
 * A configuration can contains several other configurations. In which case the
 * child configurations get factored with the parent configuration to create N
 * configurations that inherit the parameters and descriptor of the parent
 * configuration. If a child configuration specify a value already present in the
 * parent configuration, the parent configuration value will be ignored and the child
 * configuration value will be used.
 *
 * Example:
 * BazelConfiguration(["descriptor": "yeah"],
 *                    ["params1": false],
 *                    [BazelConfiguration(["descriptor2": "a"], [], [params2: true]),
 *                     BazelConfiguration(["descriptor2": "b"], [], [params1: true, params2: false])])
 *
 * would expand to the following configurations:
 *
 * BazelConfiguration(["descriptor": "yeah", "descriptor2": "a"], [params1: false, params2: true])])
 * BazelConfiguration(["descriptor": "yeah", "descriptor2": "b"], [params1: true, params2: false])])
 */
class BazelConfiguration implements java.io.Serializable {
  private Map<String, String> descriptor
  private Map<String, Object> parameters
  private List<BazelConfiguration> configurations

  private static def EMPTY_CONFIGURATION = new BazelConfiguration([:], [:], [])

  static public interface ConfigurationContainer {
    def addConfiguration(BazelConfiguration)
  }

  private static List<BazelConfiguration> parseJson(Object json) {
    List<BazelConfiguration> result = []
    for (Object o in json) {
      result.add(new BazelConfiguration(o))
    }
    return result
  }

  private static Object toSerializable(Object jsonObject) {
    // JsonSlurper map and list are not serializable, which make them unsuitable for
    // usage inside a Jenkins pipeline, convert them to HashMap and ArrayList
    if (jsonObject instanceof Map) {
      def result = [:]
      for (e in jsonObject) {
        result[e.key] = toSerializable(e.value)
      }
      return result
    } else if (jsonObject instanceof List) {
      def result = []
      for (it in jsonObject) {
        result.add(toSerializable(it))
      }
      return result
    } else {
      return jsonObject
    }
  }

  /**
   * Parse a list of configurations for a JSON string.
   * A JSON configuration is an object whose key -> values are the entries
   * of the configuration descriptor, except for "configurations" and "parameters"
   * keys which correspond respectively to the child configurations and the parameters.
   */
  public static List<BazelConfiguration> parse(String jsonString) {
    // There is a subtle bug in the parser so skip the first comment line
    while (jsonString.trim().startsWith("//")) {
      def pos = jsonString.indexOf("\n")
      jsonString = pos < 0 ? "" : jsonString.substring(pos + 1)
    }
    def jsonObject = new JsonSlurper().setType(JsonParserType.LAX).parseText(jsonString);
    return parseJson(toSerializable(jsonObject))
  }

  /** Parse a list of configurations from a JSON file. */
  public static List<BazelConfiguration> parse(File jsonFile) {
    return parse(jsonFile.text)
  }

  /**
   * Flatten a list of configurations into a map of descriptor -> parameters.
   *
   * excludeConfigurations can be used to specifically deny certain configuration.
   * A configuration will be selected only if, for any key k in the descriptor, either the k
   * is not a key of excludeConfigurations or the value of the descriptor is NOT in
   * excludeConfigurations[k].
   *
   * Examples:
   * - excludeConfigurations = ["a": ["a", "b"]] would NOT match descriptor
   *   ["a": "a"], ["a": "b"] but would match ["b": "whatever"] or ["a": "c"].
   * - excludeConfigurations = ["node": ["linux-x86_64"]] would match descriptors
   *   that DO NOT point to an execution on a linux node.
   */
  public static Map<Map<String, String>, Map<String, Object>> flattenConfigurations(
      List<BazelConfiguration> configurations,
      Map<String, List<String>> excludeConfigurations = [:]) {
    def result = [:]
    for (conf in configurations) {
      result += conf.restrict(excludeConfigurations).flatten()
    }
    return result
  }

  private BazelConfiguration(Object json) {
    this.parameters = ("parameters" in json) ? json["parameters"] : [:]
    this.configurations = ("configurations" in json) ?
        json["configurations"].collect { it -> new BazelConfiguration(it) } : []
    this.descriptor = json.findAll { k, v -> k != "configurations" && k != "parameters" }
  }

  public BazelConfiguration(Map<String, String> descriptor,
                            Map<String, Object> parameters,
                            List<BazelConfiguration> configurations = []) {
    this.descriptor = descriptor
    this.parameters = parameters
    this.configurations = configurations
  }

  def getDescriptor() {
    return descriptor
  }

  def getParameters() {
    return parameters
  }

  def getConfigurations() {
    return configurations
  }

  private boolean matchRestriction(excludeConfigurations) {
    // Avoid closures because CPS is having trouble with it
    for (def e : descriptor.entrySet()) {
      if ((e.key in excludeConfigurations) && (e.value in excludeConfigurations[e.key])) {
        return true
      }
    }
    return false
  }

  private BazelConfiguration restrict(excludeConfigurations) {
    if (!excludeConfigurations.isEmpty()) {
      if (matchRestriction(excludeConfigurations)) {
        return EMPTY_CONFIGURATION
      }
      if (configurations.isEmpty()) {
        return this
      } else {
        def newConfigs = []
        for (configuration in configurations) {
          def conf = configuration.restrict(excludeConfigurations)
          if (conf != EMPTY_CONFIGURATION) {
            newConfigs << conf
          }
        }
        if (newConfigs.isEmpty()) {
          return EMPTY_CONFIGURATION;
        } else {
          return new BazelConfiguration(descriptor, parameters, newConfigs)
        }
      }
    }
    return this
  }

  private Map<Map<String, String>, Map<String, Object>> flatten() {
    Map<Map<String, String>, Map<String, Object>> result = [:]

    if (configurations.isEmpty()) {
      if (!descriptor.isEmpty()) {
        result[descriptor] = parameters
      }
      return result
    } else {
      for (conf in configurations) {
        def configs = conf.flatten()
        for (e in configs) {
          def descr2 = [:]
          descr2.putAll(descriptor)
          descr2.putAll(e.key)
          result[descr2] = [:]
          result[descr2].putAll(parameters)
          result[descr2].putAll(e.value)
        }
      }
      if (result.isEmpty() && !descriptor.isEmpty()) {
        result[descriptor] = parameters
      }
      return result
    }
  }

  public String toString() {
    return "BazelConfiguration({descriptor=${descriptor}, parameters=${parameters}, configurations=${configurations})"
  }

  /** Convert a map descriptor to a one line description */
  @NonCPS
  public static def descriptorToString(descriptor) {
    return descriptor.collect { "${it.key}=${it.value}" }.join(",")
  }
}
