package build.bazel.dashboard.github.issue;

import io.reactivex.rxjava3.core.Maybe;
import io.reactivex.rxjava3.core.Single;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@Slf4j
public class GithubIssueRestController {
  private final GithubIssueService githubIssueService;

  @GetMapping("/internal/github/{owner}/{repo}/issues/{issueNumber}")
  public Maybe<GithubIssue> findOneGithubIssue(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @PathVariable("issueNumber") Integer issueNumber) {
    return githubIssueService
        .fetchAndSave(owner, repo, issueNumber)
        .map(GithubIssueService.FetchResult::getGithubIssue)
        .toMaybe();
  }

  @PutMapping("/internal/github/{owner}/{repo}/issues/{issueNumber}")
  public Single<GithubIssueService.FetchResult> updateGithubIssue(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @PathVariable("issueNumber") Integer issueNumber) {
    return githubIssueService.fetchAndSave(owner, repo, issueNumber);
  }

  /*
  @Builder
  @Value
  static class UpdateResult {
    int count;
    int added;
    int updated;
    int deleted;
    int untouched;
    int error;
  }

  @PutMapping("/internal/github/{owner}/{repo}/issues")
  public Single<UpdateResult> updateGithubIssues(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @RequestParam(name = "start") Integer start,
      @RequestParam(name = "count") Integer count) {
    checkNotNull(start);
    checkNotNull(count);
    return Observable.range(start, count)
        .flatMap(
            issueNumber -> githubIssueService.fetchAndSave(owner, repo, issueNumber).toObservable(),
            10) // Limit concurrent request to 10 so we won't rate limited by Github
        .collect(
            UpdateResult::builder,
            (builder, result) -> {
              if (result.isAdded()) {
                builder.added(builder.added + 1);
              } else if (result.isUpdated()) {
                builder.updated(builder.updated + 1);
              } else if (result.isDeleted()) {
                builder.deleted(builder.deleted + 1);
              } else if (result.getError() != null) {
                builder.error(builder.error + 1);
              } else {
                builder.untouched(builder.untouched + 1);
              }
            })
        .map(builder -> builder.count(count).build());
  }
   */
}
