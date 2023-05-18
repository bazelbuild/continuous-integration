package build.bazel.dashboard.github.api;

import build.bazel.dashboard.common.RestApiResponse;

public interface GithubApi {
  RestApiResponse listRepositoryIssues(ListRepositoryIssuesRequest request);

  RestApiResponse listRepositoryEvents(ListRepositoryEventsRequest request);

  RestApiResponse listRepositoryIssueEvents(ListRepositoryIssueEventsRequest request);

  RestApiResponse fetchIssue(FetchIssueRequest request);

  RestApiResponse listIssueComments(ListIssueCommentsRequest request);

  RestApiResponse searchIssues(SearchIssuesRequest request);
}
