package build.bazel.dashboard.github.api;

import build.bazel.dashboard.github.api.GetIssueRequest;
import build.bazel.dashboard.github.api.GithubApiResponse;
import build.bazel.dashboard.github.api.ListRepositoryIssuesRequest;
import reactor.core.publisher.Mono;

public interface GithubApi {
  Mono<GithubApiResponse> listRepositoryIssues(ListRepositoryIssuesRequest request);

  Mono<GithubApiResponse> getIssue(GetIssueRequest request);
}
