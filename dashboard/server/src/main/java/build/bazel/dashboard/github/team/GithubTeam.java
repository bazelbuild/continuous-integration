package build.bazel.dashboard.github.team;

import com.google.common.collect.ImmutableList;
import lombok.Builder;
import lombok.Value;

import java.time.Instant;

@Builder
@Value
public class GithubTeam {
  String owner;
  String repo;
  String label;
  Instant createdAt;
  Instant updatedAt;
  String name;
  ImmutableList<String> teamOwners;

  private static final String NONE_NAME = "(none)";

  public boolean isNone() {
    return NONE_NAME.equals(name);
  }

  public static GithubTeam buildNone(String owner, String repo, String teamOwner) {
    return GithubTeam.builder()
        .owner(owner)
        .repo(repo)
        .label("")
        .createdAt(Instant.EPOCH)
        .updatedAt(Instant.EPOCH)
        .name(NONE_NAME)
        .teamOwners(ImmutableList.of(teamOwner))
        .build();
  }
}
