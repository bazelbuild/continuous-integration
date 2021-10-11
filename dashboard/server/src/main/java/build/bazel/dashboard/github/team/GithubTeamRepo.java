package build.bazel.dashboard.github.team;

import io.reactivex.rxjava3.core.Flowable;

public interface GithubTeamRepo {
  Flowable<GithubTeam> list(String owner, String repo);
}
