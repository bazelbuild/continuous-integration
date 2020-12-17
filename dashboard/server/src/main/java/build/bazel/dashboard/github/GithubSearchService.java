package build.bazel.dashboard.github;

import io.reactivex.rxjava3.core.Single;

public interface GithubSearchService {
  Single<Integer> fetchSearchResultCount(String owner, String repo, String query);
}
