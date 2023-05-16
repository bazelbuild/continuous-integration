package build.bazel.dashboard.github.issuestatus;

import static build.bazel.dashboard.utils.RxJavaVirtualThread.completable;

import build.bazel.dashboard.github.issue.GithubIssueService;
import io.reactivex.rxjava3.core.Completable;
import java.time.Instant;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Slf4j
@RequiredArgsConstructor
public class GithubIssueStatusRestController {
  private final GithubIssueService githubIssueService;
  private final GithubIssueStatusService githubIssueStatusService;

  @PutMapping("/internal/github/{owner}/{repo}/issues/status")
  public Completable checkStatus(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @RequestParam(name = "start") Integer start,
      @RequestParam(name = "count") Integer count) {
    return completable(
        () -> {
          for (var number = start; number < start + count; ++number) {
            var issue = githubIssueService.findOne(owner, repo, number);
            if (issue.isPresent()) {
              githubIssueStatusService.check(issue.get(), Instant.now());
            }
          }
        });
  }
}
