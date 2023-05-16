package build.bazel.dashboard.buildkite.build;

import build.bazel.dashboard.buildkite.api.BuildkiteRestApiClient;
import build.bazel.dashboard.buildkite.api.FetchBuildRequest;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Instant;
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
}
