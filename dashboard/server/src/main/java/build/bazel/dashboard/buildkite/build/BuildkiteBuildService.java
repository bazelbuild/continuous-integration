package build.bazel.dashboard.buildkite.build;

import build.bazel.dashboard.buildkite.api.BuildkiteRestApiClient;
import build.bazel.dashboard.buildkite.api.FetchBuildRequest;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Instant;
import java.util.regex.Pattern;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class BuildkiteBuildService {

  private final BuildkiteRestApiClient buildkiteRestApiClient;
  private final BuildkiteBuildRepo buildkiteBuildRepo;
  private final ObjectMapper objectMapper;

  public BuildkiteBuild fetchAndSave(String org, String pipeline, int buildNumber) {
    var existing = buildkiteBuildRepo.findOne(org, pipeline, buildNumber)
        .orElse(BuildkiteBuild.empty(org, pipeline, buildNumber, objectMapper));

    var request = FetchBuildRequest.create(org, pipeline, buildNumber, existing.etag());
    var response = buildkiteRestApiClient.fetchBuild(request);
    var status = response.getStatus();
    if (status.is2xxSuccessful()) {
      var build = new BuildkiteBuild(
          org,
          pipeline,
          buildNumber,
          Instant.now(),
          response.getEtag(),
          response.getBody()
      );
      buildkiteBuildRepo.save(build);
      return build;
    } else if (status.value() == 304) {
      // Not modified
      return existing;
    }

    log.error(
        "Failed to fetch {}/{}/builds/{}: {}",
        org,
        pipeline,
        buildNumber,
        status);

    throw new RuntimeException(status.toString());
  }

  private static final Pattern BUILD_URL_PATTERN = Pattern.compile(
      "https://api.buildkite.com/v2/organizations/([^/]+)/pipelines/([^/]+)/builds/(\\d+)");

  public void onEvent(JsonNode event) {
    var eventType = event.get("event").asText();
    if (eventType.startsWith("build.")) {
      var buildJson = event.get("build");
      var buildUrl = buildJson.get("url").asText();
      var match = BUILD_URL_PATTERN.matcher(buildUrl);
      if (!match.matches()) {
        throw new IllegalArgumentException("Invalid build url: " + buildUrl);
      }
      var org = match.group(1);
      var pipeline = match.group(2);
      var buildNumber = Integer.parseInt(match.group(3));
      var unused = fetchAndSave(org, pipeline, buildNumber);
    }
  }
}
