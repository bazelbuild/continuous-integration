package build.bazel.dashboard.github.issue;

import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Maybe;
import io.reactivex.rxjava3.core.Observable;

public interface GithubIssueRepository {

  Completable save(GithubIssue githubIssue);

  Completable delete(String owner, String repo, int issueNumber);

  Maybe<GithubIssue> findOne(String owner, String repo, int issueNumber);

  Observable<GithubIssue> list();
}
