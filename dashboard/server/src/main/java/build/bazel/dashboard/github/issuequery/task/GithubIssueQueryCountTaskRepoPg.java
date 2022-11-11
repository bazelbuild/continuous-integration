package build.bazel.dashboard.github.issuequery.task;

import static com.google.common.collect.ImmutableList.toImmutableList;

import build.bazel.dashboard.utils.Period;
import com.google.common.collect.ImmutableList;
import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Flowable;
import java.time.Instant;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;
import reactor.adapter.rxjava.RxJava3Adapter;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@Repository
@RequiredArgsConstructor
public class GithubIssueQueryCountTaskRepoPg
    implements GithubIssueQueryCountTaskRepo {
  private final DatabaseClient databaseClient;

  @Override
  public ImmutableList<GithubIssueQueryCountTask> list(Period period) {
    return databaseClient
        .sql(
            "SELECT giqct.owner, giqct.repo, giqct.query_id, giqct.period, giqct.created_at,"
                + " giq.query FROM github_issue_query_count_task giqct INNER JOIN"
                + " github_issue_query giq ON giqct.owner = giq.owner AND giqct.repo = giq.repo AND"
                + " giqct.query_id = giq.id WHERE giqct.period = :period")
        .bind("period", period.toString())
        .map(
            row ->
                GithubIssueQueryCountTask.builder()
                    .owner(row.get("owner", String.class))
                    .repo(row.get("repo", String.class))
                    .queryId(row.get("query_id", String.class))
                    .period(Period.valueOf(row.get("period", String.class)))
                    .createdAt(row.get("created_at", Instant.class))
                    .query(row.get("query", String.class))
                    .build())
        .all()
        .collect(toImmutableList())
        .block();
  }

  @Override
  public void saveResult(GithubIssueQueryCountTask task, Instant timestamp, int count) {
    databaseClient
        .sql(
            "INSERT INTO github_issue_query_count_task_result (owner, repo, query_id, period,"
                + " timestamp, count) VALUES (:owner, :repo, :query_id, :period, :timestamp,"
                + " :count) ON CONFLICT (owner, repo, query_id, period, timestamp) DO UPDATE"
                + " SET count = excluded.count")
        .bind("owner", task.getOwner())
        .bind("repo", task.getRepo())
        .bind("query_id", task.getQueryId())
        .bind("period", task.getPeriod().toString())
        .bind("timestamp", task.getPeriod().truncate(timestamp))
        .bind("count", count)
        .then()
        .block();
  }

  @Override
  public ImmutableList<GithubIssueQueryCountTaskResult> listResult(
      String owner, String repo, String queryId, Period period, Instant from, Instant to) {
    return databaseClient
        .sql(
            "SELECT owner, repo, query_id, period, timestamp, count FROM"
                + " github_issue_query_count_task_result WHERE owner = :owner AND repo = :repo"
                + " AND query_id = :query_id AND period = :period AND timestamp >= :from AND"
                + " timestamp <= :to")
        .bind("owner", owner)
        .bind("repo", repo)
        .bind("query_id", queryId)
        .bind("period", period.toString())
        .bind("from", period.truncate(from))
        .bind("to", period.truncate(to))
        .map(
            row ->
                GithubIssueQueryCountTaskResult.builder()
                    .owner(row.get("owner", String.class))
                    .repo(row.get("repo", String.class))
                    .queryId(row.get("query_id", String.class))
                    .period(Period.valueOf(row.get("period", String.class)))
                    .timestamp(row.get("timestamp", Instant.class))
                    .count(row.get("count", Integer.class))
                    .build())
        .all()
        .collect(toImmutableList())
        .block();
  }
}
