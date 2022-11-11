package build.bazel.dashboard.github.issue;

import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Maybe;
import io.reactivex.rxjava3.core.Observable;
import io.reactivex.rxjava3.core.Single;
import java.io.IOException;
import java.util.Optional;

public interface GithubIssueRepo {

  void save(GithubIssue githubIssue) throws IOException;

  void delete(String owner, String repo, int issueNumber);

  Optional<GithubIssue> findOne(String owner, String repo, int issueNumber);

  Observable<GithubIssue> list();

  Integer findMaxIssueNumber(String owner, String repo);
}
