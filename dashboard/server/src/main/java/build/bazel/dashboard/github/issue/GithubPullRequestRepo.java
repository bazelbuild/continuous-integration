package build.bazel.dashboard.github.issue;

import static build.bazel.dashboard.utils.PgJson.toPgJson;
import static java.util.Objects.requireNonNull;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.r2dbc.postgresql.codec.Json;
import io.r2dbc.spi.Readable;
import java.io.IOException;
import java.time.Instant;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class GithubPullRequestRepo {
  private final DatabaseClient databaseClient;
  private final ObjectMapper objectMapper;

  public void save(GithubPullRequest pullRequest) {
    databaseClient
        .sql(
            "INSERT INTO github_pull_request_data (owner, repo, issue_number, timestamp, etag, data)"
                + " VALUES (:owner, :repo, :issue_number, :timestamp, :etag, :data) ON"
                + " CONFLICT (owner, repo, issue_number) DO UPDATE SET etag = excluded.etag,"
                + " timestamp = excluded.timestamp, data = excluded.data")
        .bind("owner", pullRequest.owner())
        .bind("repo", pullRequest.repo())
        .bind("issue_number", pullRequest.issueNumber())
        .bind("timestamp", pullRequest.timestamp())
        .bind("etag", pullRequest.etag())
        .bind("data", toPgJson(objectMapper, pullRequest.data()))
        .then()
        .block();
  }

  public void delete(String owner, String repo, int issueNumber) {
    databaseClient
        .sql(
            "DELETE FROM github_pull_request_data WHERE owner = :owner AND repo = :repo AND"
                + " issue_number = :issue_number")
        .bind("owner", owner)
        .bind("repo", repo)
        .bind("issue_number", issueNumber)
        .then()
        .block();
  }

  public Optional<GithubPullRequest> findOne(String owner, String repo, int issueNumber) {
    return Optional.ofNullable(
        databaseClient
            .sql(
                "SELECT owner, repo, issue_number, timestamp, etag, data FROM github_pull_request_data "
                    + "WHERE owner=:owner AND repo=:repo AND issue_number=:issue_number")
            .bind("owner", owner)
            .bind("repo", repo)
            .bind("issue_number", issueNumber)
            .map(this::toPullRequest)
            .one()
            .block());
  }

  private GithubPullRequest toPullRequest(Readable row) {
    try {
      return new GithubPullRequest(
          requireNonNull(row.get("owner", String.class)),
          requireNonNull(row.get("repo", String.class)),
          requireNonNull(row.get("issue_number", Integer.class)),
          requireNonNull(row.get("timestamp", Instant.class)),
          requireNonNull(row.get("etag", String.class)),
          objectMapper.readTree((requireNonNull(row.get("data", Json.class))).asArray()));
    } catch (IOException e) {
      throw new IllegalStateException(e);
    }
  }
}
