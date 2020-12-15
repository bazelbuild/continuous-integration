package build.bazel.dashboard.github.issue;

import io.reactivex.rxjava3.core.Single;

public interface GithubSearchExecutor {
  Single<Integer> fetchSearchResultCount(String owner, String repo, String query);
}
