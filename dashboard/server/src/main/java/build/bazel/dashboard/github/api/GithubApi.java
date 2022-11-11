package build.bazel.dashboard.github.api;

public interface GithubApi {
  GithubApiResponse listRepositoryIssues(ListRepositoryIssuesRequest request);

  GithubApiResponse listRepositoryEvents(ListRepositoryEventsRequest request);

  GithubApiResponse listRepositoryIssueEvents(ListRepositoryIssueEventsRequest request);

  GithubApiResponse fetchIssue(FetchIssueRequest request);

  GithubApiResponse listIssueComments(ListIssueCommentsRequest request);

  GithubApiResponse searchIssues(SearchIssuesRequest request);
}
