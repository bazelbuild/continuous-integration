package build.bazel.dashboard.github.issue;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.r2dbc.postgresql.codec.Json;
import io.r2dbc.spi.Row;
import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Maybe;
import io.reactivex.rxjava3.core.Observable;
import io.reactivex.rxjava3.core.Single;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;
import reactor.adapter.rxjava.RxJava3Adapter;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.io.IOException;
import java.time.Instant;

import static java.util.Objects.requireNonNull;

@Repository
@RequiredArgsConstructor
public class GithubIssueRepoPg implements GithubIssueRepo {

  private final DatabaseClient databaseClient;
  private final ObjectMapper objectMapper;

  @Override
  public Completable save(GithubIssue githubIssue) {
    try {
      Mono<Void> execution =
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
              .then();
      return RxJava3Adapter.monoToCompletable(execution);
    } catch (JsonProcessingException e) {
      return Completable.error(e);
    }
  }

  @Override
  public Completable delete(String owner, String repo, int issueNumber) {
    Mono<Void> execution =
        databaseClient
            .sql(
                "DELETE FROM github_issue_data WHERE owner = :owner AND repo = :repo AND"
                    + " issue_number = :issue_number")
            .bind("owner", owner)
            .bind("repo", repo)
            .bind("issue_number", issueNumber)
            .then();
    return RxJava3Adapter.monoToCompletable(execution);
  }

  @Override
  public Maybe<GithubIssue> findOne(String owner, String repo, int issueNumber) {
    Mono<GithubIssue> query =
        databaseClient
            .sql(
                "SELECT owner, repo, issue_number, timestamp, etag, data FROM github_issue_data "
                    + "WHERE owner=:owner AND repo=:repo AND issue_number=:issue_number")
            .bind("owner", owner)
            .bind("repo", repo)
            .bind("issue_number", issueNumber)
            .map(this::toGithubIssue)
            .one();
    return RxJava3Adapter.monoToMaybe(query);
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

  private GithubIssue toGithubIssue(Row row) {
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
  public Single<Integer> findMaxIssueNumber(String owner, String repo) {
    Mono<Integer> query =
        databaseClient
            .sql(
                "SELECT COALESCE(MAX(issue_number), 0) as max_issue_number FROM github_issue WHERE owner ="
                    + " :owner AND repo = :repo")
            .bind("owner", owner)
            .bind("repo", repo)
            .map(row -> row.get("max_issue_number", Integer.class))
            .one();
    return RxJava3Adapter.monoToSingle(query);
  }
}
