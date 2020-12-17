package build.bazel.dashboard.github.db.postgresql;

import build.bazel.dashboard.github.GithubIssueQuery;
import build.bazel.dashboard.github.db.GithubIssueQueryRepository;
import io.reactivex.rxjava3.core.Maybe;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;
import reactor.adapter.rxjava.RxJava3Adapter;
import reactor.core.publisher.Mono;

import java.time.Instant;

@Repository
@RequiredArgsConstructor
public class PostgresqlGithubQueryRepository implements GithubIssueQueryRepository {
  private final DatabaseClient databaseClient;

  @Override
  public Maybe<GithubIssueQuery> findOne(String owner, String repo, String id) {
    Mono<GithubIssueQuery> query =
        databaseClient
            .sql(
                "SELECT owner, repo, id, created_at, updated_at, name, query FROM github_issue_query WHERE owner = :owner AND repo = :repo AND id = :id")
            .bind("owner", owner)
            .bind("repo", repo)
            .bind("id", id)
            .map(
                row ->
                    GithubIssueQuery.builder()
                        .owner(row.get("owner", String.class))
                        .repo(row.get("repo", String.class))
                        .id(row.get("id", String.class))
                        .createdAt(row.get("created_at", Instant.class))
                        .updatedAt(row.get("updated_at", Instant.class))
                        .name(row.get("name", String.class))
                        .query(row.get("query", String.class))
                        .build())
            .one();
    return RxJava3Adapter.monoToMaybe(query);
  }
}
