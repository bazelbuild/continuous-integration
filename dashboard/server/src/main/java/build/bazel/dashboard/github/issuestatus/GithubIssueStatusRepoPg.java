package build.bazel.dashboard.github.issuestatus;

import static java.util.Objects.requireNonNull;

import com.google.common.collect.ImmutableList;
import io.r2dbc.spi.Readable;
import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Maybe;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;
import reactor.adapter.rxjava.RxJava3Adapter;
import reactor.core.publisher.Mono;

@Repository
@RequiredArgsConstructor
public class GithubIssueStatusRepoPg implements GithubIssueStatusRepo {

  private final DatabaseClient databaseClient;

  @Override
  public void save(GithubIssueStatus status) {
    Deque<String> actionOwners = new ArrayDeque<>(status.getActionOwners());
    String actionOwner = null;
    if (!actionOwners.isEmpty()) {
      actionOwner = actionOwners.removeFirst();
    }
    DatabaseClient.GenericExecuteSpec spec =
        databaseClient
            .sql(
                "INSERT INTO github_issue_status (owner, repo, issue_number, status, action_owner,"
                    + " more_action_owners, updated_at, expected_respond_at, last_notified_at,"
                    + " next_notify_at, checked_at) VALUES (:owner, :repo, :issue_number, :status,"
                    + " :action_owner, :more_action_owners, :updated_at, :expected_respond_at,"
                    + " :last_notified_at, :next_notify_at,  :checked_at) ON CONFLICT (owner, repo,"
                    + " issue_number) DO UPDATE SET status = excluded.status, action_owner ="
                    + " excluded.action_owner, more_action_owners = excluded.more_action_owners,"
                    + " updated_at = excluded.updated_at, expected_respond_at ="
                    + " excluded.expected_respond_at, last_notified_at = excluded.last_notified_at,"
                    + " next_notify_at = excluded.next_notify_at, checked_at = excluded.checked_at")
            .bind("owner", status.getOwner())
            .bind("repo", status.getRepo())
            .bind("issue_number", status.getIssueNumber())
            .bind("more_action_owners", actionOwners.toArray(new String[0]))
            .bind("status", status.getStatus().toString())
            .bind("updated_at", status.getUpdatedAt())
            .bind("checked_at", status.getCheckedAt());

    if (actionOwner != null) {
      spec = spec.bind("action_owner", actionOwner);
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

    spec.then().block();
  }

  @Override
  public Optional<GithubIssueStatus> findOne(String owner, String repo, int issueNumber) {
    return Optional.ofNullable(
        databaseClient
            .sql(
                "SELECT owner, repo, issue_number, status, action_owner, more_action_owners,"
                    + " updated_at, expected_respond_at, last_notified_at, next_notify_at,"
                    + " checked_at FROM github_issue_status WHERE owner = :owner AND repo = :repo"
                    + " AND issue_number = :issue_number")
            .bind("owner", owner)
            .bind("repo", repo)
            .bind("issue_number", issueNumber)
            .map(this::toGithubIssueStatus)
            .one()
            .block());
  }

  private GithubIssueStatus toGithubIssueStatus(Readable row) {
    ImmutableList.Builder<String> actionOwners = new ImmutableList.Builder<>();
    String actionOwner = row.get("action_owner", String.class);
    if (actionOwner != null && !actionOwner.isBlank()) {
      actionOwners.add(actionOwner);
    }
    actionOwners.add(requireNonNull(row.get("more_action_owners", String[].class)));

    return GithubIssueStatus.builder()
        .owner(requireNonNull(row.get("owner", String.class)))
        .repo(requireNonNull(row.get("repo", String.class)))
        .issueNumber(requireNonNull(row.get("issue_number", Integer.class)))
        .status(GithubIssueStatus.Status.valueOf(row.get("status", String.class)))
        .actionOwners(actionOwners.build())
        .updatedAt(requireNonNull(row.get("updated_at", Instant.class)))
        .expectedRespondAt(row.get("expected_respond_at", Instant.class))
        .lastNotifiedAt(row.get("last_notified_at", Instant.class))
        .nextNotifyAt(row.get("next_notify_at", Instant.class))
        .checkedAt(requireNonNull(row.get("checked_at", Instant.class)))
        .build();
  }
}
