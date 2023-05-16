package build.bazel.dashboard.github.issuequery;

import static build.bazel.dashboard.utils.RxJavaVirtualThread.maybe;
import static build.bazel.dashboard.utils.RxJavaVirtualThread.single;

import build.bazel.dashboard.github.issuequery.GithubIssueQueryExecutor.QueryResult;
import io.reactivex.rxjava3.core.Maybe;
import io.reactivex.rxjava3.core.Single;
import lombok.RequiredArgsConstructor;
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

  @GetMapping("/internal/github/{owner}/{repo}/search")
  public Single<QueryResult> search(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @RequestParam(name = "q") String q) {
    return single(() -> githubIssueQueryExecutor.execute(owner, repo, q));
  }

  @GetMapping("/internal/github/{owner}/{repo}/search/{queryId}")
  public Maybe<QueryResult> searchByQueryId(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @PathVariable("queryId") String queryId) {
    return maybe(
        () ->
            githubIssueQueryRepo
                .findOne(owner, repo, queryId)
                .map(query -> githubIssueQueryExecutor.execute(owner, repo, query.getQuery())));
  }
}
