package build.bazel.dashboard.buildkite.build;

import build.bazel.dashboard.buildkite.api.BuildkiteRestApiClient;
import build.bazel.dashboard.buildkite.api.FetchBuildRequest;
import build.bazel.dashboard.buildkite.build.BuildkiteBuildRepo.BuildStats;
import build.bazel.dashboard.common.RestApiResponse;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.time.Instant;
import java.util.List;
import java.util.regex.Pattern;
import javax.annotation.Nullable;
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

  public static class FetchException extends IOException {

    private final RestApiResponse response;

    public FetchException(RestApiResponse response) {
      super("Failed to fetch: " + response);
      this.response = response;
    }

    public RestApiResponse getResponse() {
      return response;
    }
  }

  public BuildkiteBuild fetchAndSave(String org, String pipeline, int buildNumber)
      throws FetchException {
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

    throw new FetchException(response);
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
      try {
        var unused = fetchAndSave(org, pipeline, buildNumber);
      } catch (FetchException e) {
        log.error("{}", e.getMessage());
      }
    }
  }

  public BuildStats findBuildStats(String org, String pipeline, @Nullable String branch, @Nullable Instant from,
      @Nullable Instant to) {
    if (from == null) {
      from = Instant.EPOCH;
    }
    if (to == null) {
      to = Instant.now();
    }
    return buildkiteBuildRepo.findBuildStats(org, pipeline, branch, from, to);
  }
}
