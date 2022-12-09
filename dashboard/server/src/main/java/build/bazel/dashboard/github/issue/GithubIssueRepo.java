package build.bazel.dashboard.github.issue;

import io.reactivex.rxjava3.core.Observable;
import java.util.Optional;

public interface GithubIssueRepo {

  void save(GithubIssue githubIssue);

  void delete(String owner, String repo, int issueNumber);

  Optional<GithubIssue> findOne(String owner, String repo, int issueNumber);

  Observable<GithubIssue> list();

  Integer findMaxIssueNumber(String owner, String repo);
}
