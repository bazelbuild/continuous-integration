package build.bazel.dashboard.github;

import lombok.Builder;
import lombok.Value;

import java.time.Instant;

@Builder
@Value
public class GithubIssueTeam {
  String owner;
  String repo;
  String label;
  Instant createdAt;
  Instant updatedAt;
  String name;
  String teamOwner;

  public static GithubIssueTeam buildNone(String owner, String repo) {
    return GithubIssueTeam.builder()
        .owner(owner)
        .repo(repo)
        .label("")
        .createdAt(Instant.EPOCH)
        .updatedAt(Instant.EPOCH)
        .name("(none)")
        .teamOwner("")
        .build();
  }
}
