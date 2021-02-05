package build.bazel.dashboard.github.db;

import build.bazel.dashboard.github.team.GithubTeam;
import io.reactivex.rxjava3.core.Flowable;

public interface GithubIssueTeamRepository {
  Flowable<GithubTeam> list(String owner, String repo);
}
