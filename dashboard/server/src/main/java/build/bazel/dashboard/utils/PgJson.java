package build.bazel.dashboard.utils;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.TextNode;
import com.google.common.collect.Iterables;
import com.google.common.collect.Iterators;
import io.r2dbc.postgresql.codec.Json;
import java.util.Map;

public class PgJson {

  private PgJson() {}

  public static Json toPgJson(ObjectMapper objectMapper, Object value) {
    var tree = replaceNul(objectMapper, objectMapper.valueToTree(value));
    return Json.of(tree.toString());
  }

  private static JsonNode replaceNul(ObjectMapper objectMapper, JsonNode node) {
    if (node.isTextual()) {
      return TextNode.valueOf(node.asText().replaceAll("\u0000", ""));
    } else if (node.isArray()) {
      var array = objectMapper.createArrayNode();
      for (var child : Iterables.transform(node, child -> PgJson.replaceNul(objectMapper, child))) {
        array.add(child);
      }
      return array;
    } else if (node.isObject()) {
      var object = objectMapper.createObjectNode();
      var it = Iterators.transform(
          node.fields(), field -> Map.entry(field.getKey(), replaceNul(objectMapper, field.getValue())));
      while (it.hasNext()) {
        var field = it.next();
        object.set(field.getKey(), field.getValue());
      }
      return object;
    } else {
      return node;
    }
  }
}
