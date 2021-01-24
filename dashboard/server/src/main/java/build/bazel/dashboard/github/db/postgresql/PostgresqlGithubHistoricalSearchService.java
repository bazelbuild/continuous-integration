package build.bazel.dashboard.github.db.postgresql;

import build.bazel.dashboard.github.GithubHistoricalSearchService;
import build.bazel.dashboard.github.GithubQueryParser;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.r2dbc.postgresql.codec.Json;
import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Single;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;
import reactor.adapter.rxjava.RxJava3Adapter;
import reactor.core.publisher.Flux;

import java.io.IOException;
import java.time.Instant;
import java.util.List;

import static build.bazel.dashboard.github.GithubQueryParser.*;
import static java.util.Objects.requireNonNull;

@Repository
@Slf4j
@RequiredArgsConstructor
public class PostgresqlGithubHistoricalSearchService implements GithubHistoricalSearchService {
  private final ObjectMapper objectMapper;
  private final DatabaseClient databaseClient;
  private final GithubQueryParser queryParser;

  @NoArgsConstructor
  @Data
  static class GithubIssue {
    int number;
    String state;
    PullRequest pull_request;
    List<Label> labels;

    public boolean getIsPullRequest() {
      return pull_request != null;
    }

    public boolean containsLabel(String label) {
      for (Label myLabel : labels) {
        if (label.equals(myLabel.getName())) {
          return true;
        }
      }

      return false;
    }

    @NoArgsConstructor
    @Data
    static class Label {
      String name;
    }

    @NoArgsConstructor
    @Data
    static class PullRequest {
      String name;
    }
  }

  @Override
  public Single<Integer> fetchSearchResultCount(
      String owner, String repo, String query, Instant timestamp) {

    Query parsedQuery = queryParser.parse(query);

    // We fetch all the issues for a given repo. Since the number of issues for a repo would be too
    // large (about 10K for
    // bazelbuild/bazel), we are able to load them all into memory.
    return fetchAllIssues(owner, repo, timestamp)
        .filter(githubIssue -> filter(parsedQuery, githubIssue))
        .count()
        .map(Long::intValue);
  }

  private boolean filter(Query query, GithubIssue githubIssue) {
    if (query.getState() != null) {
      if (!query.getState().equals(githubIssue.getState())) {
        return false;
      }
    }

    if (query.getIsPullRequest() != null) {
      if (query.getIsPullRequest() != githubIssue.getIsPullRequest()) {
        return false;
      }
    }

    for (String label : query.getLabels()) {
      if (!githubIssue.containsLabel(label)) {
        return false;
      }
    }

    for (String label : query.getExcludeLabels()) {
      if (githubIssue.containsLabel(label)) {
        return false;
      }
    }

    return true;
  }

  private Flowable<GithubIssue> fetchAllIssues(String owner, String repo, Instant timestamp) {
    Flux<GithubIssue> query =
        databaseClient
            .sql(
                "WITH data AS ("
                    + "SELECT data, ROW_NUMBER() OVER (PARTITION BY issue_number ORDER BY timestamp DESC) AS row "
                    + "FROM github_issue_data_snapshot "
                    + "WHERE owner = :owner "
                    + "AND repo = :repo "
                    + "AND timestamp < :timestamp"
                    + ") SELECT * FROM data WHERE row = 1")
            .bind("owner", owner)
            .bind("repo", repo)
            .bind("timestamp", timestamp)
            .map(
                row -> {
                  try {
                    return objectMapper.readValue(
                        requireNonNull(row.get("data", Json.class)).asArray(), GithubIssue.class);
                  } catch (IOException e) {
                    throw new RuntimeException(e);
                  }
                })
            .all();
    return RxJava3Adapter.fluxToFlowable(query);
  }
}
