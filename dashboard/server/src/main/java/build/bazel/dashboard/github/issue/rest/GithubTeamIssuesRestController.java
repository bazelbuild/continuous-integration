package build.bazel.dashboard.github.issue.rest;

import build.bazel.dashboard.github.issue.*;
import build.bazel.dashboard.github.task.PollGithubEventsTask;
import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Maybe;
import io.reactivex.rxjava3.core.Observable;
import io.reactivex.rxjava3.core.Single;
import lombok.Builder;
import lombok.RequiredArgsConstructor;
import lombok.Value;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import static com.google.common.base.Preconditions.checkNotNull;

@RestController
@RequiredArgsConstructor
@Slf4j
public class GithubTeamIssuesRestController {
  private final GithubTeamIssueProvider githubTeamIssueProvider;
  private final GithubIssueRepository githubIssueRepository;
  private final PollGithubEventsTask pollGithubEventsTask;
  private final GithubIssueFetcher githubIssueFetcher;

  @GetMapping("/github/teams/issues")
  public Observable<GithubTeamIssue> listGithubTeamIssues() {
    return githubTeamIssueProvider.list();
  }

  @GetMapping("/github/{owner}/{repo}/issues/{issueNumber}")
  public Maybe<GithubIssue> findOneGithubIssue(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @PathVariable("issueNumber") Integer issueNumber) {
    return githubIssueRepository.findOne(owner, repo, issueNumber);
  }

  @PutMapping("/github/{owner}/{repo}/events")
  public Completable pollGithubRepositoryEvents(
      @PathVariable("owner") String owner, @PathVariable("repo") String repo) {
    return pollGithubEventsTask.pollGithubRepositoryEvents(owner, repo);
  }

  @PutMapping("/github/{owner}/{repo}/issues/{issueNumber}")
  public Single<GithubIssueFetcher.FetchResult> updateGithubIssue(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @PathVariable("issueNumber") Integer issueNumber) {
    return githubIssueFetcher.fetch(owner, repo, issueNumber);
  }

  @Builder
  @Value
  static class UpdateResult {
    int count;
    int added;
    int updated;
    int untouched;
    int error;
  }

  private Maybe<GithubIssue> fetchOneIssues(String owner, String repo, Integer issueNumber) {
    return githubIssueFetcher
        .fetch(owner, repo, issueNumber)
        .map(GithubIssueFetcher.FetchResult::getGithubIssue)
        .toMaybe();
  }

  @PutMapping("/github/{owner}/{repo}/issues")
  public Single<UpdateResult> updateGithubIssues(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @RequestParam(name = "start") Integer start,
      @RequestParam(name = "count") Integer count) {
    checkNotNull(start);
    checkNotNull(count);
    return Observable.range(start, count)
        .flatMap(
            issueNumber -> githubIssueFetcher.fetch(owner, repo, issueNumber).toObservable(),
            10) // Limit concurrent request to 10 so we won't rate limited by Github
        .collect(
            UpdateResult::builder,
            (builder, result) -> {
              if (result.isAdded()) {
                builder.added(builder.added + 1);
              } else if (result.isUpdated()) {
                builder.updated(builder.updated + 1);
              } else if (result.getError() != null) {
                builder.error(builder.error + 1);
              } else {
                builder.untouched(builder.untouched + 1);
              }
            })
        .map(builder -> builder.count(count).build());
  }
}
