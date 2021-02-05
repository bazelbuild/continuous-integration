package build.bazel.dashboard.github.issuequery;

import io.reactivex.rxjava3.core.Single;

public interface GithubIssueQueryExecutor {
  Single<Integer> fetchQueryResultCount(String owner, String repo, String query);
}
