package build.bazel.dashboard.github.teamtable;

import static build.bazel.dashboard.github.teamtable.GithubTeamTable.Cell;

import build.bazel.dashboard.github.GithubUtils;
import build.bazel.dashboard.github.issuequery.GithubIssueQueryExecutor;
import build.bazel.dashboard.github.team.GithubTeam;
import build.bazel.dashboard.github.team.GithubTeamService;
import build.bazel.dashboard.github.teamtable.GithubTeamTable.Row;
import build.bazel.dashboard.github.teamtable.GithubTeamTableRepo.GithubTeamTableData;
import com.github.benmanes.caffeine.cache.AsyncCache;
import com.github.benmanes.caffeine.cache.Caffeine;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.Lists;
import java.time.Duration;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.stream.Collectors;
import jdk.incubator.concurrent.StructuredTaskScope;
import lombok.Builder;
import lombok.RequiredArgsConstructor;
import lombok.Value;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Service
@Slf4j
@RequiredArgsConstructor
public class GithubTeamTableService {
  private final GithubTeamTableRepo githubTeamTableRepo;
  private final GithubTeamService githubTeamService;
  private final GithubIssueQueryExecutor githubIssueQueryExecutor;

  @Builder
  @Value
  static class GithubTeamTableCacheKey {
    String owner;
    String repo;
    String tableId;
  }

  private final AsyncCache<GithubTeamTableCacheKey, GithubTeamTable> tableCache =
      Caffeine.newBuilder()
          .expireAfterWrite(Duration.ofSeconds(1))
          .executor(Executors.newVirtualThreadPerTaskExecutor())
          .buildAsync();

  public GithubTeamTable findOne(String owner, String repo, String tableId) {
    try {
      return tableCache
          .get(
              GithubTeamTableCacheKey.builder().owner(owner).repo(repo).tableId(tableId).build(),
              (key) -> loadOne(key.getOwner(), key.getRepo(), key.getTableId()))
          .get();
    } catch (InterruptedException | ExecutionException e) {
      throw new RuntimeException(e);
    }
  }

  GithubTeamTable loadOne(String owner, String repo, String tableId) {
    return githubTeamTableRepo
        .findOne(owner, repo, tableId)
        .map(
            table -> {
              var teams = findAllTeams(owner, repo, table.getNoneTeamOwner());
              return fetchTable(teams, table);
            })
        .orElseGet(() -> GithubTeamTable.buildNone(owner, repo, tableId, ""));
  }

  private GithubTeamTable fetchTable(List<GithubTeam> teams, GithubTeamTableData table) {
    var rows = Lists.<Row>newArrayListWithExpectedSize(teams.size());
    try (var scope = new StructuredTaskScope<>()) {
      var futures = ImmutableList.<Future<Row>>builderWithExpectedSize(teams.size());
      for (var team : teams) {
        var future = scope.fork(() -> fetchRow(teams, team, table));
        futures.add(future);
      }

      try {
        scope.join();

        for (var future : futures.build()) {
          rows.add(future.get());
        }
      } catch (InterruptedException | ExecutionException e) {
        throw new RuntimeException(e);
      }
    }

    rows.sort(Comparator.comparing(row -> row.getTeam().getName()));
    return GithubTeamTable.builder()
        .owner(table.getOwner())
        .repo(table.getRepo())
        .id(table.getId())
        .name(table.getName())
        .headers(
            table.getHeaders().stream()
                .map(
                    header ->
                        GithubTeamTable.Header.builder()
                            .id(header.getId())
                            .name(header.getName())
                            .build())
                .collect(Collectors.toList()))
        .rows(rows)
        .build();
  }

  record CellEntry(String headerId, Cell cell) {}

  private Row fetchRow(List<GithubTeam> teams, GithubTeam team, GithubTeamTableData table) {
    var cells = new HashMap<String, Cell>();
    try (var scope = new StructuredTaskScope<>()) {
      var futures =
          ImmutableList.<Future<CellEntry>>builderWithExpectedSize(table.getHeaders().size());
      for (var header : table.getHeaders()) {
        String query = interceptQuery(teams, team, header.getQuery());
        var future =
            scope.fork(
                () -> {
                  var count =
                      githubIssueQueryExecutor.fetchQueryResultCount(
                          team.getOwner(), team.getRepo(), query);
                  return new CellEntry(
                      header.getId(),
                      Cell.builder()
                          .url(
                              GithubUtils.buildIssueQueryUrl(
                                  team.getOwner(), team.getRepo(), query))
                          .count(count)
                          .build());
                });
        futures.add(future);
      }
      try {
        scope.join();

        for (var future : futures.build()) {
          var entry = future.get();
          cells.put(entry.headerId, entry.cell);
        }
      } catch (InterruptedException | ExecutionException e) {
        throw new RuntimeException(e);
      }
    }

    return Row.builder().team(GithubTeamTable.Team.create(team)).cells(cells).build();
  }

  private String interceptQuery(List<GithubTeam> teams, GithubTeam team, String query) {
    String teamQuery;
    if (team.isNone()) {
      teamQuery =
          teams.stream()
              .map(GithubTeam::getLabel)
              .filter(label -> !label.equals(""))
              .map(label -> "-label:" + label)
              .collect(Collectors.joining(" "));
    } else {
      teamQuery = "label:" + team.getLabel();
    }

    return String.format("%s %s", query, teamQuery);
  }

  private ImmutableList<GithubTeam> findAllTeams(String owner, String repo, String noneTeamOwner) {
    var teams = githubTeamService.findAll(owner, repo);
    return ImmutableList.<GithubTeam>builderWithExpectedSize(teams.size() + 1)
        .addAll(teams)
        .add(GithubTeam.buildNone(owner, repo, noneTeamOwner))
        .build();
  }
}
