package build.bazel.dashboard.github.db;

import build.bazel.dashboard.github.GithubIssueQuery;
import io.reactivex.rxjava3.core.Maybe;

public interface GithubIssueQueryRepository {
  Maybe<GithubIssueQuery> findOne(String owner, String repo, String id);
}
