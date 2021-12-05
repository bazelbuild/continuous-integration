package build.bazel.dashboard.github.api;

import io.reactivex.rxjava3.core.Single;

public interface GithubApi {
  Single<GithubApiResponse> listRepositoryIssues(ListRepositoryIssuesRequest request);

  Single<GithubApiResponse> listRepositoryEvents(ListRepositoryEventsRequest request);

  Single<GithubApiResponse> listRepositoryIssueEvents(ListRepositoryIssueEventsRequest request);

  Single<GithubApiResponse> fetchIssue(FetchIssueRequest request);

  Single<GithubApiResponse> listIssueComments(ListIssueCommentsRequest request);

  Single<GithubApiResponse> searchIssues(SearchIssuesRequest request);
}
