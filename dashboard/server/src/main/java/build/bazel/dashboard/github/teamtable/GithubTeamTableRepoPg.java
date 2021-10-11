package build.bazel.dashboard.github.teamtable;

import build.bazel.dashboard.github.teamtable.GithubTeamTableRepo.GithubTeamTableData.Header;
import io.reactivex.rxjava3.core.Maybe;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;
import reactor.adapter.rxjava.RxJava3Adapter;
import reactor.core.publisher.Mono;

import java.time.Instant;
import java.util.Comparator;
import java.util.stream.Collectors;

@Repository
@RequiredArgsConstructor
public class GithubTeamTableRepoPg implements GithubTeamTableRepo {
  private final DatabaseClient databaseClient;

  @Override
  public Maybe<GithubTeamTableData> findOne(String owner, String repo, String tableId) {
    Mono<GithubTeamTableData> query =
        databaseClient
            .sql(
                "SELECT owner, repo, id, created_at, updated_at, name, none_team_owner FROM github_team_table WHERE"
                    + " owner = :owner AND repo = :repo AND id = :id")
            .bind("owner", owner)
            .bind("repo", repo)
            .bind("id", tableId)
            .map(
                row ->
                    GithubTeamTableData.builder()
                        .owner(row.get("owner", String.class))
                        .repo(row.get("repo", String.class))
                        .id(row.get("id", String.class))
                        .createdAt(row.get("created_at", Instant.class))
                        .updatedAt(row.get("updated_at", Instant.class))
                        .name(row.get("name", String.class))
                        .noneTeamOwner(row.get("none_team_owner", String.class)))
            .one()
            .flatMap(
                builder -> {
                  GithubTeamTableData tmp = builder.build();
                  return databaseClient
                      .sql(
                          "SELECT id, created_at, updated_at, seq, name, query FROM"
                              + " github_team_table_header WHERE owner = :owner AND repo = :repo"
                              + " AND table_id = :tableId")
                      .bind("owner", tmp.getOwner())
                      .bind("repo", tmp.getRepo())
                      .bind("tableId", tmp.getId())
                      .map(
                          row ->
                              Header.builder()
                                  .id(row.get("id", String.class))
                                  .createdAt(row.get("created_at", Instant.class))
                                  .updatedAt(row.get("updated_at", Instant.class))
                                  .seq(row.get("seq", Integer.class))
                                  .name(row.get("name", String.class))
                                  .query(row.get("query", String.class))
                                  .build())
                      .all()
                      .collect(Collectors.toList())
                      .map(headers -> {
                        headers.sort(Comparator.comparing(Header::getSeq));
                        return builder.headers(headers).build();
                      });
                });

    return RxJava3Adapter.monoToMaybe(query);
  }
}
