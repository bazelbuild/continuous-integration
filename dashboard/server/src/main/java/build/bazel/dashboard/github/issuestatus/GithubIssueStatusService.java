package build.bazel.dashboard.github.issuestatus;

import build.bazel.dashboard.github.issue.GithubIssue;
import build.bazel.dashboard.github.issue.GithubIssue.Label;
import build.bazel.dashboard.github.issue.GithubIssue.User;
import build.bazel.dashboard.github.issue.GithubIssueService;
import build.bazel.dashboard.github.issuestatus.GithubIssueStatus.GithubIssueStatusBuilder;
import build.bazel.dashboard.github.issuestatus.GithubIssueStatus.Status;
import build.bazel.dashboard.github.team.GithubTeam;
import build.bazel.dashboard.github.team.GithubTeamService;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Maybe;
import io.reactivex.rxjava3.core.Single;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Nullable;
import java.time.Instant;
import java.util.List;

import static java.time.temporal.ChronoUnit.DAYS;

@Service
@Slf4j
@RequiredArgsConstructor
public class GithubIssueStatusService {
  private final ObjectMapper objectMapper;
  private final GithubIssueStatusRepo githubIssueStatusRepo;
  private final GithubTeamService githubTeamService;

  public Maybe<GithubIssueStatus> findOne(String owner, String repo, int issueNumber) {
    return githubIssueStatusRepo.findOne(owner, repo, issueNumber);
  }

  public Maybe<GithubIssueStatus> check(GithubIssue issue, Instant now) {
    String owner = issue.getOwner();
    String repo = issue.getRepo();

    if (!(owner.equals("bazelbuild") && repo.equals("bazel"))) {
      return Maybe.empty();
    }

    return githubIssueStatusRepo
        .findOne(owner, repo, issue.getIssueNumber())
        .flatMapSingle(status -> buildStatus(status, issue, now))
        .switchIfEmpty(buildStatus(null, issue, now))
        .flatMapMaybe(status -> githubIssueStatusRepo.save(status).andThen(Maybe.just(status)));
  }

  public Completable markDeleted(String owner, String repo, int issueNumber) {
    return githubIssueStatusRepo
        .findOne(owner, repo, issueNumber)
        .flatMapCompletable(
            status -> {
              status.status = Status.DELETED;
              return githubIssueStatusRepo.save(status);
            });
  }

  private Single<GithubIssueStatus> buildStatus(
      @Nullable GithubIssueStatus oldStatus, GithubIssue issue, Instant now) {
    return Single.fromCallable(() -> issue.parseData(objectMapper))
        .flatMap(
            data -> {
              Status newStatus = newStatus(data);
              Instant lastNotifiedAt = null;

              if (oldStatus != null) {
                lastNotifiedAt = oldStatus.getLastNotifiedAt();
              }

              Instant expectedRespondAt = getExpectedRespondAt(data, newStatus);
              Instant nextNotifyAt = expectedRespondAt;

              if (lastNotifiedAt != null
                  && nextNotifyAt != null
                  && lastNotifiedAt.isAfter(expectedRespondAt)) {
                nextNotifyAt = lastNotifiedAt.plus(1, DAYS);
              }

              GithubIssueStatusBuilder builder =
                  GithubIssueStatus.builder()
                      .owner(issue.getOwner())
                      .repo(issue.getRepo())
                      .issueNumber(issue.getIssueNumber())
                      .status(newStatus)
                      .updatedAt(data.getUpdatedAt())
                      .expectedRespondAt(expectedRespondAt)
                      .lastNotifiedAt(lastNotifiedAt)
                      .nextNotifyAt(nextNotifyAt)
                      .checkedAt(now);

              return findActionOwner(issue, data, newStatus)
                  .map(builder::actionOwner)
                  .defaultIfEmpty(builder)
                  .map(GithubIssueStatusBuilder::build);
            });
  }

  static Status newStatus(GithubIssue.Data data) {
    if (data.getState().equals("closed")) {
      return Status.CLOSED;
    }

    List<Label> labels = data.getLabels();

    if (hasMoreDataNeededLabel(labels)) {
      return Status.MORE_DATA_NEEDED;
    }

    if (hasTeamLabel(labels)) {
      if (hasPriorityLabel(labels)) {
        return Status.TRIAGED;
      } else {
        return Status.REVIEWED;
      }
    }

    return Status.TO_BE_REVIEWED;
  }

  // TODO: More serious business days handling
  static @Nullable Instant getExpectedRespondAt(GithubIssue.Data data, Status status) {
    Instant updatedAt = data.getUpdatedAt();

    switch (status) {
      case TO_BE_REVIEWED:
      case MORE_DATA_NEEDED:
      case REVIEWED:
        return updatedAt.plus(7, DAYS);
      case TRIAGED:
        {
          List<Label> labels = data.getLabels();
          if (hasLabelPrefix(labels, "P0")) {
            return updatedAt.plus(1, DAYS);
          } else if (hasLabelPrefix(labels, "P1")) {
            return updatedAt.plus(7, DAYS);
          } else if (hasLabelPrefix(labels, "P2")) {
            return updatedAt.plus(120, DAYS);
          }

          return null;
        }

      default:
    }

    return null;
  }

  private Maybe<String> findActionOwner(GithubIssue issue, GithubIssue.Data data, Status status) {
    switch (status) {
      case TO_BE_REVIEWED:
        return Maybe.empty();
      case MORE_DATA_NEEDED:
        return Maybe.just(data.getUser().getLogin());
      case REVIEWED:
      case TRIAGED:
        User assignee = data.getAssignee();
        if (assignee != null) {
          return Maybe.just(assignee.getLogin());
        } else {
          List<Label> labels = data.getLabels();
          return githubTeamService
              .findAll(issue.getOwner(), issue.getRepo())
              .filter(
                  team ->
                      labels.stream().anyMatch(label -> label.getName().equals(team.getLabel())))
              .firstElement()
              .map(GithubTeam::getTeamOwner);
        }
    }

    return Maybe.empty();
  }

  private static boolean hasTeamLabel(List<Label> labels) {
    return hasLabelPrefix(labels, "team-");
  }

  private static boolean hasMoreDataNeededLabel(List<Label> labels) {
    return hasLabelPrefix(labels, "\"more data needed\"");
  }

  private static boolean hasPriorityLabel(List<Label> labels) {
    return hasLabelPrefix(labels, "P");
  }

  private static boolean hasLabelPrefix(List<Label> labels, String prefix) {
    for (Label label : labels) {
      if (label.getName().startsWith(prefix)) {
        return true;
      }
    }

    return false;
  }
}
