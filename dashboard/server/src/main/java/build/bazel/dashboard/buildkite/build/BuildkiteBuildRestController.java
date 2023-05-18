package build.bazel.dashboard.buildkite.build;

import static build.bazel.dashboard.utils.RxJavaVirtualThread.maybe;
import static build.bazel.dashboard.utils.RxJavaVirtualThread.single;

import build.bazel.dashboard.buildkite.build.BuildkiteBuildRepo.BuildStats;
import io.reactivex.rxjava3.core.Maybe;
import io.reactivex.rxjava3.core.Single;
import java.time.Instant;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
public class BuildkiteBuildRestController {
  private final BuildkiteBuildService buildkiteBuildService;

  @GetMapping("/internal/buildkite/organizations/{org}/pipelines/{pipeline}/builds/{buildNumber}")
  public Maybe<BuildkiteBuild> findOneGithubIssue(
      @PathVariable("org") String org,
      @PathVariable("pipeline") String pipeline,
      @PathVariable("buildNumber") Integer buildNumber) {
    return maybe(
        () ->
            Optional.ofNullable(
                buildkiteBuildService.fetchAndSave(org, pipeline, buildNumber)));
  }

  @GetMapping("/buildkite/organizations/{org}/pipelines/{pipeline}/stats")
  public Single<BuildStats> findBuildStats(
      @PathVariable("org") String org,
      @PathVariable("pipeline") String pipeline,
      @RequestParam(value = "branch", required = false) String branch,
      @RequestParam(value = "from", required = false) Instant from,
      @RequestParam(value = "to", required = false) Instant to
  ) {
    return single(() -> buildkiteBuildService.findBuildStats(org, pipeline, branch, from, to));
  }
}
