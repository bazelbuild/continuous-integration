package build.bazel.dashboard.github.issuequery;

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

@RestController
@Slf4j
@RequiredArgsConstructor
public class GithubIssueQueryRestController {

  private final GithubIssueQueryExecutor githubIssueQueryExecutor;
  private final GithubIssueQueryRepo githubIssueQueryRepo;

  @Builder
  @Value
  static class SearchResult {
    int count;
  }

  @GetMapping("/internal/github/{owner}/{repo}/search")
  public Single<SearchResult> search(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @RequestParam(name = "q") String q) {
    return githubIssueQueryExecutor
        .fetchQueryResultCount(owner, repo, q)
        .map(count -> SearchResult.builder().count(count).build());
  }

  @GetMapping("/internal/github/{owner}/{repo}/search/{queryId}")
  public Maybe<SearchResult> searchByQueryId(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @PathVariable("queryId") String queryId) {
    return githubIssueQueryRepo
        .findOne(owner, repo, queryId)
        .flatMapSingle(
            query -> githubIssueQueryExecutor.fetchQueryResultCount(owner, repo, query.getQuery()))
        .map(count -> SearchResult.builder().count(count).build());
  }
}
