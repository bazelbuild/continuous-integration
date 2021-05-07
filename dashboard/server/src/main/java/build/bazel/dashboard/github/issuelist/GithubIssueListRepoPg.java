package build.bazel.dashboard.github.issuelist;

import build.bazel.dashboard.github.issuestatus.GithubIssueStatus;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.r2dbc.postgresql.codec.Json;
import io.r2dbc.spi.Row;
import io.reactivex.rxjava3.core.Single;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;
import reactor.adapter.rxjava.RxJava3Adapter;
import reactor.core.publisher.Flux;

import java.io.IOException;
import java.time.Instant;
import java.util.stream.Collectors;

import static java.util.Objects.requireNonNull;

@Repository
@RequiredArgsConstructor
public class GithubIssueListRepoPg implements GithubIssueListRepo {

  private final ObjectMapper objectMapper;
  private final DatabaseClient databaseClient;

  @Override
  public Single<GithubIssueList> find(String owner, String repo) {
    Flux<GithubIssueList.Item> query =
        databaseClient
            .sql(
                "SELECT gid.owner, gid.repo, gid.issue_number, gis.status, gis.action_owner,"
                    + " gis.expected_respond_at, gid.data FROM github_issue_status gis INNER JOIN"
                    + " github_issue gi ON (gi.owner, gi.repo, gi.issue_number) = (gis.owner,"
                    + " gis.repo, gis.issue_number) INNER JOIN github_issue_data gid ON (gid.owner,"
                    + " gid.repo, gid.issue_number) = (gi.owner, gi.repo, gi.issue_number)"
                    + " WHERE gis.owner = :owner AND gis.repo = :repo")
            .bind("owner", owner)
            .bind("repo", repo)
            .map(this::toGithubIssueListItem)
            .all();
    return RxJava3Adapter.fluxToFlowable(query)
        .collect(Collectors.toList())
        .map(items -> GithubIssueList.builder().items(items).build());
  }

  private GithubIssueList.Item toGithubIssueListItem(Row row) {
    try {
      return GithubIssueList.Item.builder()
          .owner(requireNonNull(row.get("owner", String.class)))
          .repo(requireNonNull(row.get("repo", String.class)))
          .issueNumber(requireNonNull(row.get("issue_number", Integer.class)))
          .status(GithubIssueStatus.Status.valueOf(row.get("status", String.class)))
          .actionOwner(row.get("action_owner", String.class))
          .expectedRespondAt(row.get("expected_respond_at", Instant.class))
          .data(objectMapper.readTree((requireNonNull(row.get("data", Json.class))).asArray()))
          .build();
    } catch (IOException e) {
      throw new IllegalStateException(e);
    }
  }
}
