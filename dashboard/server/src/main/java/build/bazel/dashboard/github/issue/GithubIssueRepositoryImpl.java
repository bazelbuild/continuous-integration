package build.bazel.dashboard.github.issue;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.r2dbc.postgresql.codec.Json;
import io.r2dbc.spi.Row;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.io.IOException;
import java.time.Instant;

import static java.util.Objects.requireNonNull;

@Component
@RequiredArgsConstructor
public class GithubIssueRepositoryImpl implements GithubIssueRepository {

  private final DatabaseClient databaseClient;
  private final ObjectMapper objectMapper;

  @Override
  public Mono<GithubIssue> save(GithubIssue githubIssue) {
    return insertOrUpdate(githubIssue).thenReturn(githubIssue);
  }

  private Mono<Void> insertOrUpdate(GithubIssue githubIssue) {
    try {
      return databaseClient
          .sql(
              "INSERT INTO github_issue_data (owner, repo, issue_number, timestamp, etag, data) "
                  + "VALUES (:owner, :repo, :issue_number, :timestamp, :etag, :data) "
                  + "ON CONFLICT (owner, repo, issue_number) DO UPDATE "
                  + "SET etag = excluded.etag, timestamp = excluded.timestamp, data = excluded.data")
          .bind("owner", githubIssue.getOwner())
          .bind("repo", githubIssue.getRepo())
          .bind("issue_number", githubIssue.getIssueNumber())
          .bind("timestamp", githubIssue.getTimestamp())
          .bind("etag", githubIssue.getETag())
          .bind("data", Json.of(objectMapper.writeValueAsBytes(githubIssue.getData())))
          .then();
    } catch (JsonProcessingException e) {
      return Mono.error(e);
    }
  }

  @Override
  public Mono<GithubIssue> findOne(String owner, String repo, int issueNumber) {
    return databaseClient
        .sql(
            "SELECT owner, repo, issue_number, timestamp, etag, data FROM github_issue_data "
                + "WHERE owner=:owner AND repo=:repo AND issue_number=:issue_number")
        .bind("owner", owner)
        .bind("repo", repo)
        .bind("issue_number", issueNumber)
        .map(this::toGithubIssue)
        .one();
  }

  @Override
  public Flux<GithubIssue> list() {
    return databaseClient
        // language=SQL
        .sql("SELECT owner, repo, issue_number, timestamp, etag, data FROM github_issue_data")
        .map(this::toGithubIssue)
        .all();
  }

  private GithubIssue toGithubIssue(Row row) {
    try {
      return GithubIssue.builder()
          .owner(requireNonNull(row.get("owner", String.class)))
          .repo(requireNonNull(row.get("repo", String.class)))
          .issueNumber(requireNonNull(row.get("issue_number", Integer.class)))
          .timestamp(requireNonNull(row.get("timestamp", Instant.class)))
          .eTag(requireNonNull(row.get("etag", String.class)))
          .data(objectMapper.readTree((requireNonNull(row.get("data", Json.class))).asArray()))
          .build();
    } catch (IOException e) {
      throw new IllegalStateException(e);
    }
  }
}
