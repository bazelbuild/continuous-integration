package build.bazel.dashboard.github.team;

import build.bazel.dashboard.github.team.GithubTeam;
import io.reactivex.rxjava3.core.Flowable;

public interface GithubTeamRepo {
  Flowable<GithubTeam> list(String owner, String repo);
}
