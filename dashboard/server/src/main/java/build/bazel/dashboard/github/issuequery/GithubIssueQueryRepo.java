package build.bazel.dashboard.github.issuequery;

import io.reactivex.rxjava3.core.Maybe;

public interface GithubIssueQueryRepo {
  Maybe<GithubIssueQuery> findOne(String owner, String repo, String id);
}
