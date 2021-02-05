package build.bazel.dashboard.github.teamtable;

import build.bazel.dashboard.github.issuequery.GithubIssueQueryExecutor;
import build.bazel.dashboard.github.GithubUtils;
import build.bazel.dashboard.github.team.GithubTeam;
import build.bazel.dashboard.github.team.GithubTeamService;
import build.bazel.dashboard.github.teamtable.GithubTeamTable.Row;
import build.bazel.dashboard.github.teamtable.GithubTeamTableRepo.GithubTeamTableData;
import build.bazel.dashboard.utils.RxJavaFutures;
import com.github.benmanes.caffeine.cache.AsyncCache;
import com.github.benmanes.caffeine.cache.Caffeine;
import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Single;
import lombok.Builder;
import lombok.RequiredArgsConstructor;
import lombok.Value;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.AbstractMap;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;

import static build.bazel.dashboard.github.teamtable.GithubTeamTable.Cell;

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

  private final AsyncCache<GithubTeamTableCacheKey, GithubTeamTable> issueCache =
      Caffeine.newBuilder().expireAfterWrite(Duration.ofSeconds(1)).buildAsync();

  Single<GithubTeamTable> findOne(String owner, String repo, String tableId) {
    return Single.fromFuture(
        issueCache.get(
            GithubTeamTableCacheKey.builder().owner(owner).repo(repo).tableId(tableId).build(),
            (key, executor) ->
                RxJavaFutures.toCompletableFuture(
                    loadOne(key.getOwner(), key.getRepo(), key.getTableId()), executor)));
  }

  Single<GithubTeamTable> loadOne(String owner, String repo, String tableId) {
    return githubTeamTableRepo
        .findOne(owner, repo, tableId)
        .flatMapSingle(
            table -> findAllTeams(owner, repo).flatMap(teams -> fetchTable(teams, table)))
        .defaultIfEmpty(GithubTeamTable.buildNone(owner, repo, tableId));
  }

  private Single<GithubTeamTable> fetchTable(List<GithubTeam> teams, GithubTeamTableData table) {
    return Flowable.fromIterable(teams)
        .flatMapSingle(team -> fetchRow(teams, team, table))
        .collect(Collectors.toList())
        .map(
            rows ->
                GithubTeamTable.builder()
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
                    .build());
  }

  private Single<Row> fetchRow(List<GithubTeam> teams, GithubTeam team, GithubTeamTableData table) {
    return Flowable.fromIterable(table.getHeaders())
        .flatMapSingle(
            header -> {
              String query = interceptQuery(teams, team, header.getQuery());
              return githubIssueQueryExecutor
                  .fetchQueryResultCount(team.getOwner(), team.getRepo(), query)
                  .map(
                      count ->
                          new AbstractMap.SimpleEntry<>(
                              header.getId(),
                              Cell.builder()
                                  .url(
                                      GithubUtils.buildIssueQueryUrl(
                                          team.getOwner(), team.getRepo(), query))
                                  .count(count)
                                  .build()));
            })
        .collect(
            Collectors.toMap(AbstractMap.SimpleEntry::getKey, AbstractMap.SimpleEntry::getValue))
        .map(
            cells ->
                Row.builder()
                    .team(
                        GithubTeamTable.Team.builder()
                            .name(team.getName())
                            .teamOwner(team.getTeamOwner())
                            .build())
                    .cells(cells)
                    .build());
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

  private Single<List<GithubTeam>> findAllTeams(String owner, String repo) {
    return githubTeamService
        .findAll(owner, repo)
        .collect(Collectors.toList())
        .doOnSuccess(
            teams -> {
              teams.add(GithubTeam.buildNone(owner, repo));
              teams.sort(Comparator.comparing(GithubTeam::getName));
            });
  }
}
