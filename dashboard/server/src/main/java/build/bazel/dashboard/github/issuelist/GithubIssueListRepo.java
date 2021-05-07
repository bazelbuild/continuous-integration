package build.bazel.dashboard.github.issuelist;

import io.reactivex.rxjava3.core.Single;

public interface GithubIssueListRepo {
  Single<GithubIssueList> find(String owner, String repo);
}
