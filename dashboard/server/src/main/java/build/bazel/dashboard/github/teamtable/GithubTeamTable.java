package build.bazel.dashboard.github.teamtable;

import build.bazel.dashboard.github.team.GithubTeam;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import lombok.Builder;
import lombok.Value;

import java.util.List;
import java.util.Map;

@Builder
@Value
public class GithubTeamTable {
  String owner;
  String repo;
  String id;
  String name;
  List<Header> headers;
  List<Row> rows;

  public static GithubTeamTable buildNone(String owner, String repo, String id) {
    return GithubTeamTable.builder()
        .owner(owner)
        .repo(repo)
        .id(id)
        .name("")
        .headers(ImmutableList.of())
        .rows(
            ImmutableList.of(
                Row.builder()
                    .team(Team.create(GithubTeam.buildNone(owner, repo)))
                    .cells(ImmutableMap.of())
                    .build()))
        .build();
  }

  @Builder
  @Value
  public static class Header {
    String id;
    String name;
  }

  @Builder
  @Value
  public static class Row {
    Team team;
    Map<String, Cell> cells;
  }

  @Builder
  @Value
  public static class Team {
    String name;
    String teamOwner;

    public static Team create(GithubTeam team) {
      return Team.builder()
          .name(team.getName())
          .teamOwner(team.getTeamOwner())
          .build();
    }
  }

  @Builder
  @Value
  public static class Cell {
    String url;
    Integer count;
  }
}
