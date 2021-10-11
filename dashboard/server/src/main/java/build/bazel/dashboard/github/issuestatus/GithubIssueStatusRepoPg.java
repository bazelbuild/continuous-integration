package build.bazel.dashboard.github.issuestatus;

import io.r2dbc.spi.Row;
import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Maybe;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;
import reactor.adapter.rxjava.RxJava3Adapter;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Instant;

import static java.util.Objects.requireNonNull;

@Repository
@RequiredArgsConstructor
public class GithubIssueStatusRepoPg implements GithubIssueStatusRepo {

  private final DatabaseClient databaseClient;

  @Override
  public Completable save(GithubIssueStatus status) {
    DatabaseClient.GenericExecuteSpec spec =
        databaseClient
            .sql(
                "INSERT INTO github_issue_status (owner, repo, issue_number, status, action_owner,"
                    + " updated_at, expected_respond_at, last_notified_at, next_notify_at,"
                    + " checked_at) VALUES (:owner, :repo, :issue_number, :status, :action_owner,"
                    + " :updated_at, :expected_respond_at, :last_notified_at, :next_notify_at, "
                    + " :checked_at) ON CONFLICT (owner, repo, issue_number) DO UPDATE SET status ="
                    + " excluded.status, action_owner = excluded.action_owner, updated_at ="
                    + " excluded.updated_at, expected_respond_at = excluded.expected_respond_at,"
                    + " last_notified_at = excluded.last_notified_at, next_notify_at ="
                    + " excluded.next_notify_at, checked_at = excluded.checked_at")
            .bind("owner", status.getOwner())
            .bind("repo", status.getRepo())
            .bind("issue_number", status.getIssueNumber())
            .bind("status", status.getStatus().toString())
            .bind("updated_at", status.getUpdatedAt())
            .bind("checked_at", status.getCheckedAt());

    if (status.getActionOwner() != null) {
      spec = spec.bind("action_owner", status.getActionOwner());
    } else {
      spec = spec.bindNull("action_owner", String.class);
    }

    if (status.getExpectedRespondAt() != null) {
      spec = spec.bind("expected_respond_at", status.getExpectedRespondAt());
    } else {
      spec = spec.bindNull("expected_respond_at", Instant.class);
    }

    if (status.getLastNotifiedAt() != null) {
      spec = spec.bind("last_notified_at", status.getLastNotifiedAt());
    } else {
      spec = spec.bindNull("last_notified_at", Instant.class);
    }

    if (status.getNextNotifyAt() != null) {
      spec = spec.bind("next_notify_at", status.getNextNotifyAt());
    } else {
      spec = spec.bindNull("next_notify_at", Instant.class);
    }

    return RxJava3Adapter.monoToCompletable(spec.then());
  }

  @Override
  public Maybe<GithubIssueStatus> findOne(String owner, String repo, int issueNumber) {
    Mono<GithubIssueStatus> query =
        databaseClient
            .sql(
                "SELECT owner, repo, issue_number, status, action_owner, updated_at,"
                    + " expected_respond_at, last_notified_at, next_notify_at, checked_at FROM"
                    + " github_issue_status WHERE owner = :owner AND repo = :repo AND issue_number"
                    + " = :issue_number")
            .bind("owner", owner)
            .bind("repo", repo)
            .bind("issue_number", issueNumber)
            .map(this::toGithubIssueStatus)
            .one();
    return RxJava3Adapter.monoToMaybe(query);
  }

  private GithubIssueStatus toGithubIssueStatus(Row row) {
    return GithubIssueStatus.builder()
        .owner(requireNonNull(row.get("owner", String.class)))
        .repo(requireNonNull(row.get("repo", String.class)))
        .issueNumber(requireNonNull(row.get("issue_number", Integer.class)))
        .status(GithubIssueStatus.Status.valueOf(row.get("status", String.class)))
        .actionOwner(row.get("action_owner", String.class))
        .updatedAt(requireNonNull(row.get("updated_at", Instant.class)))
        .expectedRespondAt(row.get("expected_respond_at", Instant.class))
        .lastNotifiedAt(row.get("last_notified_at", Instant.class))
        .nextNotifyAt(row.get("next_notify_at", Instant.class))
        .checkedAt(requireNonNull(row.get("checked_at", Instant.class)))
        .build();
  }
}
