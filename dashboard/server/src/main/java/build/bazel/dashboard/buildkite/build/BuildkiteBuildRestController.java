package build.bazel.dashboard.buildkite.build;

import static build.bazel.dashboard.utils.RxJavaVirtualThread.maybe;

import io.reactivex.rxjava3.core.Maybe;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
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
}
