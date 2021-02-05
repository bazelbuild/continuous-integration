package build.bazel.dashboard.github.teamtable;

import build.bazel.dashboard.github.teamtable.GithubTeamTableRepo.GithubTeamTableData.Header;
import com.google.common.collect.ImmutableList;
import io.reactivex.rxjava3.core.Maybe;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;
import reactor.adapter.rxjava.RxJava3Adapter;
import reactor.core.publisher.Mono;

import java.time.Instant;
import java.util.List;
import java.util.stream.Collectors;

@Repository
@RequiredArgsConstructor
public class GithubTeamTableRepoPg implements GithubTeamTableRepo {
  private final DatabaseClient databaseClient;

  private final List<GithubTeamTableData> data =
      ImmutableList.of(
          GithubTeamTableData.builder()
              .owner("bazelbuild")
              .repo("bazel")
              .id("open-issues")
              .name("Open Issues by Team")
              .headers(
                  ImmutableList.of(
                      Header.builder().id("total").name("Total").query("is:issue is:open").build(),
                      Header.builder()
                          .id("p0")
                          .name("P0")
                          .query("is:issue is:open label:P0")
                          .build(),
                      Header.builder()
                          .id("p1")
                          .name("P1")
                          .query("is:issue is:open label:P1")
                          .build(),
                      Header.builder()
                          .id("p2")
                          .name("P2")
                          .query("is:issue is:open label:P2")
                          .build(),
                      Header.builder()
                          .id("p3")
                          .name("P3")
                          .query("is:issue is:open label:P3")
                          .build(),
                      Header.builder()
                          .id("p4")
                          .name("P4")
                          .query("is:issue is:open label:P4")
                          .build(),
                      Header.builder()
                          .id("no-type")
                          .name("No Type")
                          .query(
                              "is:issue is:open "
                                  + "-label:\"type: process\" "
                                  + "-label:\"type: support / not a bug (process)\" "
                                  + "-label:\"type: documentation (cleanup)\" "
                                  + "-label:\"type: bug\" "
                                  + "-label:\"type: feature request\" ")
                          .build(),
                      Header.builder()
                          .id("no-priority")
                          .name("No Priority")
                          .query(
                              "is:issue is:open "
                                  + "-label:P0 "
                                  + "-label:P1 "
                                  + "-label:P2 "
                                  + "-label:P3 "
                                  + "-label:P4 ")
                          .build(),
                      Header.builder()
                          .id("untriaged")
                          .name("Untriaged")
                          .query("is:issue is:open label:untriaged")
                          .build(),
                      Header.builder().id("pr").name("PR").query("is:pr is:open").build()))
              .build());

  @Override
  public Maybe<GithubTeamTableData> findOne(String owner, String repo, String tableId) {
    Mono<GithubTeamTableData> query =
        databaseClient
            .sql(
                "SELECT owner, repo, id, created_at, updated_at, name FROM github_team_table WHERE"
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
                        .name(row.get("name", String.class)))
            .one()
            .flatMap(
                builder -> {
                  GithubTeamTableData tmp = builder.build();
                  return databaseClient
                      .sql(
                          "SELECT id, created_at, updated_at, name, query FROM"
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
                                  .name(row.get("name", String.class))
                                  .query(row.get("query", String.class))
                                  .build())
                      .all()
                      .collect(Collectors.toList())
                      .map(headers -> builder.headers(headers).build());
                });

    return RxJava3Adapter.monoToMaybe(query);
  }
}
