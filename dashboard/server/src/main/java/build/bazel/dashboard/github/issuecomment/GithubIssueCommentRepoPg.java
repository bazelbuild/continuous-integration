package build.bazel.dashboard.github.issuecomment;

import static build.bazel.dashboard.utils.PgJson.toPgJson;
import static java.util.Objects.requireNonNull;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.r2dbc.postgresql.codec.Json;
import io.r2dbc.spi.Readable;
import io.reactivex.rxjava3.core.Flowable;
import java.io.IOException;
import java.time.Instant;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;
import reactor.adapter.rxjava.RxJava3Adapter;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@Repository
@RequiredArgsConstructor
public class GithubIssueCommentRepoPg implements GithubIssueCommentRepo {

  private final DatabaseClient databaseClient;
  private final ObjectMapper objectMapper;

  @Override
  public Optional<GithubIssueCommentPage> findOnePage(
      String owner, String repo, int issueNumber, int page) {
    Mono<GithubIssueCommentPage> query =
        databaseClient
            .sql(
                "SELECT owner, repo, issue_number, page, timestamp, etag, data FROM"
                    + " github_issue_comment_data WHERE owner=:owner AND repo=:repo AND"
                    + " issue_number=:issue_number AND page=:page")
            .bind("owner", owner)
            .bind("repo", repo)
            .bind("issue_number", issueNumber)
            .bind("page", page)
            .map(this::toGithubIssueCommentPage)
            .one();
    return Optional.ofNullable(query.block());
  }

  @Override
  public Flowable<GithubIssueCommentPage> findAllPages(String owner, String repo, int issueNumber) {
    Flux<GithubIssueCommentPage> query =
        databaseClient
            .sql(
                "SELECT owner, repo, issue_number, page, timestamp, etag, data FROM"
                    + " github_issue_comment_data WHERE owner=:owner AND repo=:repo AND"
                    + " issue_number=:issue_number")
            .bind("owner", owner)
            .bind("repo", repo)
            .bind("issue_number", issueNumber)
            .map(this::toGithubIssueCommentPage)
            .all();
    return RxJava3Adapter.fluxToFlowable(query);
  }

  private GithubIssueCommentPage toGithubIssueCommentPage(Readable row) {
    try {
      return GithubIssueCommentPage.builder()
          .owner(requireNonNull(row.get("owner", String.class)))
          .repo(requireNonNull(row.get("repo", String.class)))
          .issueNumber(requireNonNull(row.get("issue_number", Integer.class)))
          .page(requireNonNull(row.get("page", Integer.class)))
          .timestamp(requireNonNull(row.get("timestamp", Instant.class)))
          .etag(requireNonNull(row.get("etag", String.class)))
          .data(objectMapper.readTree((requireNonNull(row.get("data", Json.class))).asArray()))
          .build();
    } catch (IOException e) {
      throw new IllegalStateException(e);
    }
  }

  @Override
  public void savePage(GithubIssueCommentPage page) {
    Mono<Void> execution =
        databaseClient
            .sql(
                "INSERT INTO github_issue_comment_data (owner, repo, issue_number, page,"
                    + " timestamp, etag, data) VALUES (:owner, :repo, :issue_number, :page,"
                    + " :timestamp, :etag, :data) ON CONFLICT (owner, repo, issue_number, page)"
                    + " DO UPDATE SET etag = excluded.etag, timestamp = excluded.timestamp, data"
                    + " = excluded.data")
            .bind("owner", page.getOwner())
            .bind("repo", page.getRepo())
            .bind("issue_number", page.getIssueNumber())
            .bind("page", page.getPage())
            .bind("timestamp", page.getTimestamp())
            .bind("etag", page.getEtag())
            .bind("data", toPgJson(objectMapper, page.getData()))
            .then();
    execution.block();
  }
}
