package build.bazel.dashboard.github.issuequery;

import java.time.Instant;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class GithubIssueQueryRepoPg implements GithubIssueQueryRepo {
  private final DatabaseClient databaseClient;

  @Override
  public Optional<GithubIssueQuery> findOne(String owner, String repo, String id) {
    return Optional.ofNullable(
        databaseClient
            .sql(
                "SELECT owner, repo, id, created_at, updated_at, name, query FROM"
                    + " github_issue_query WHERE owner = :owner AND repo = :repo AND id = :id")
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
            .one()
            .block());
  }
}
