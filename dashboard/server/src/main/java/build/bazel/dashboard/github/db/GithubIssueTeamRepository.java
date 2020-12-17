package build.bazel.dashboard.github.db;

import build.bazel.dashboard.github.GithubIssueTeam;
import io.reactivex.rxjava3.core.Observable;

public interface GithubIssueTeamRepository {
  Observable<GithubIssueTeam> list(String owner, String repo);
}
