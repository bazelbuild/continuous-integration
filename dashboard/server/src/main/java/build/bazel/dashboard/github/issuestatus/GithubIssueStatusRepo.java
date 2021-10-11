package build.bazel.dashboard.github.issuestatus;

import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Maybe;

public interface GithubIssueStatusRepo {
  Completable save(GithubIssueStatus status);

  Maybe<GithubIssueStatus> findOne(String owner, String repo, int issueNumber);
}
