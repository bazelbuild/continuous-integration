package build.bazel.dashboard.github.issue;

import static java.util.Objects.requireNonNull;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.r2dbc.postgresql.codec.Json;
import io.r2dbc.spi.Readable;
import io.reactivex.rxjava3.core.Observable;
import java.io.IOException;
import java.time.Instant;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;
import reactor.adapter.rxjava.RxJava3Adapter;
import reactor.core.publisher.Flux;

@Repository
@RequiredArgsConstructor
public class GithubIssueRepoPg implements GithubIssueRepo {

  private final DatabaseClient databaseClient;
  private final ObjectMapper objectMapper;

  @Override
  public void save(GithubIssue githubIssue) throws IOException {
    databaseClient
        .sql(
            "INSERT INTO github_issue_data (owner, repo, issue_number, timestamp, etag, data)"
                + " VALUES (:owner, :repo, :issue_number, :timestamp, :etag, :data) ON"
                + " CONFLICT (owner, repo, issue_number) DO UPDATE SET etag = excluded.etag,"
                + " timestamp = excluded.timestamp, data = excluded.data")
        .bind("owner", githubIssue.getOwner())
        .bind("repo", githubIssue.getRepo())
        .bind("issue_number", githubIssue.getIssueNumber())
        .bind("timestamp", githubIssue.getTimestamp())
        .bind("etag", githubIssue.getEtag())
        .bind("data", Json.of(objectMapper.writeValueAsBytes(githubIssue.getData())))
        .then()
        .block();
  }

  @Override
  public void delete(String owner, String repo, int issueNumber) {
    databaseClient
        .sql(
            "DELETE FROM github_issue_data WHERE owner = :owner AND repo = :repo AND"
                + " issue_number = :issue_number")
        .bind("owner", owner)
        .bind("repo", repo)
        .bind("issue_number", issueNumber)
        .then()
        .block();
  }

  @Override
  public Optional<GithubIssue> findOne(String owner, String repo, int issueNumber) {
    return Optional.ofNullable(
        databaseClient
            .sql(
                "SELECT owner, repo, issue_number, timestamp, etag, data FROM github_issue_data "
                    + "WHERE owner=:owner AND repo=:repo AND issue_number=:issue_number")
            .bind("owner", owner)
            .bind("repo", repo)
            .bind("issue_number", issueNumber)
            .map(this::toGithubIssue)
            .one()
            .block());
  }

  @Override
  public Observable<GithubIssue> list() {
    Flux<GithubIssue> query =
        databaseClient
            .sql("SELECT owner, repo, issue_number, timestamp, etag, data FROM github_issue_data")
            .map(this::toGithubIssue)
            .all();

    return RxJava3Adapter.fluxToObservable(query);
  }

  private GithubIssue toGithubIssue(Readable row) {
    try {
      return GithubIssue.builder()
          .owner(requireNonNull(row.get("owner", String.class)))
          .repo(requireNonNull(row.get("repo", String.class)))
          .issueNumber(requireNonNull(row.get("issue_number", Integer.class)))
          .timestamp(requireNonNull(row.get("timestamp", Instant.class)))
          .etag(requireNonNull(row.get("etag", String.class)))
          .data(objectMapper.readTree((requireNonNull(row.get("data", Json.class))).asArray()))
          .build();
    } catch (IOException e) {
      throw new IllegalStateException(e);
    }
  }

  @Override
  public Integer findMaxIssueNumber(String owner, String repo) {
    return databaseClient
        .sql(
            "SELECT COALESCE(MAX(issue_number), 0) as max_issue_number FROM github_issue WHERE"
                + " owner = :owner AND repo = :repo")
        .bind("owner", owner)
        .bind("repo", repo)
        .map(row -> row.get("max_issue_number", Integer.class))
        .one()
        .block();
  }
}
