package build.bazel.dashboard.github.team;

import com.google.common.collect.ImmutableList;

public interface GithubTeamRepo {
  ImmutableList<GithubTeam> list(String owner, String repo);
}
