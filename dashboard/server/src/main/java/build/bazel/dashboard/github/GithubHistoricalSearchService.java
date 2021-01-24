package build.bazel.dashboard.github;

import io.reactivex.rxjava3.core.Single;

import java.time.Instant;

public interface GithubHistoricalSearchService {
  Single<Integer> fetchSearchResultCount(String owner, String repo, String query, Instant timestamp);
}
