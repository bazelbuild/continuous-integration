package build.bazel.dashboard.github.rest;

import build.bazel.dashboard.github.GithubHistoricalSearchService;
import build.bazel.dashboard.github.GithubSearchService;
import build.bazel.dashboard.github.db.GithubIssueQueryRepository;
import io.reactivex.rxjava3.core.Maybe;
import io.reactivex.rxjava3.core.Single;
import lombok.Builder;
import lombok.RequiredArgsConstructor;
import lombok.Value;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;

@RestController
@Slf4j
@RequiredArgsConstructor
public class GithubIssueQueryRestController {

  private final GithubSearchService githubSearchService;
  private final GithubHistoricalSearchService githubHistoricalSearchService;
  private final GithubIssueQueryRepository githubIssueQueryRepository;

  @Builder
  @Value
  static class SearchResult {
    int count;
  }

  @GetMapping("/github/{owner}/{repo}/search")
  public Single<SearchResult> search(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @RequestParam(name = "q") String q,
      @RequestParam(value = "timestamp", required = false) Instant timestamp) {
    if (timestamp == null) {
      return githubSearchService
          .fetchSearchResultCount(owner, repo, q)
          .map(count -> SearchResult.builder().count(count).build());
    } else {
      return githubHistoricalSearchService
          .fetchSearchResultCount(owner, repo, q, timestamp)
          .map(count -> SearchResult.builder().count(count).build());
    }
  }

  @GetMapping("/github/{owner}/{repo}/search/{queryId}")
  public Maybe<SearchResult> searchByQueryId(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @PathVariable("queryId") String queryId,
      @RequestParam(value = "timestamp", required = false) Instant timestamp) {
    return githubIssueQueryRepository
        .findOne(owner, repo, queryId)
        .flatMapSingle(
            query -> {
              if (timestamp == null) {
                return githubSearchService.fetchSearchResultCount(owner, repo, query.getQuery());
              } else {
                return githubHistoricalSearchService.fetchSearchResultCount(
                    owner, repo, query.getQuery(), timestamp);
              }
            })
        .map(count -> SearchResult.builder().count(count).build());
  }
}
