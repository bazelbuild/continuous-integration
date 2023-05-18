package build.bazel.dashboard.buildkite.build;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;

public record BuildkiteBuild(
    String org,
    String pipeline,
    int buildNumber,
    Instant timestamp,
    String etag,
    JsonNode data
) {

  public static BuildkiteBuild empty(String org, String pipeline, int buildNumber,
      ObjectMapper objectMapper) {
    return new BuildkiteBuild(org, pipeline, buildNumber, Instant.now(), "",
        objectMapper.createObjectNode());
  }
}
