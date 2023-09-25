package build.bazel.dashboard.github.issuestatus;

import static java.time.temporal.ChronoUnit.DAYS;

import build.bazel.dashboard.github.issue.GithubIssue;
import build.bazel.dashboard.github.issue.GithubIssue.Label;
import build.bazel.dashboard.github.issue.GithubIssue.User;
import build.bazel.dashboard.github.issue.GithubPullRequest;
import build.bazel.dashboard.github.issuestatus.GithubIssueStatus.Status;
import build.bazel.dashboard.github.repo.GithubRepo;
import build.bazel.dashboard.github.repo.GithubRepoService;
import build.bazel.dashboard.github.team.GithubTeamService;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.common.collect.ImmutableList;
import java.io.IOException;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import javax.annotation.Nullable;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Service
@Slf4j
@RequiredArgsConstructor
public class GithubIssueStatusService {
  private final ObjectMapper objectMapper;
  private final GithubRepoService githubRepoService;
  private final GithubIssueStatusRepo githubIssueStatusRepo;
  private final GithubTeamService githubTeamService;

  public Optional<GithubIssueStatus> findOne(String owner, String repo, int issueNumber) {
    return githubIssueStatusRepo.findOne(owner, repo, issueNumber);
  }

  public Optional<GithubIssueStatus> check(
      GithubIssue issue, @Nullable GithubPullRequest pullRequest, Instant now) throws IOException {
    String owner = issue.getOwner();
    String repo = issue.getRepo();

    var githubRepoOptional = githubRepoService.findOne(owner, repo);
    if (githubRepoOptional.isEmpty()) {
      return Optional.empty();
    }

    var githubRepo = githubRepoOptional.get();
    var existingIssueStatus = githubIssueStatusRepo.findOne(owner, repo, issue.getIssueNumber());

    var newIssueStatus =
        buildStatus(githubRepo, existingIssueStatus.orElse(null), issue, pullRequest, now);
    githubIssueStatusRepo.save(newIssueStatus);
    return Optional.of(newIssueStatus);
  }

  public void markDeleted(String owner, String repo, int issueNumber) {
    githubIssueStatusRepo.findOne(owner, repo, issueNumber).ifPresent(status -> {
      status.status = Status.DELETED;
      githubIssueStatusRepo.save(status);
    });
  }

  private GithubIssueStatus buildStatus(
      GithubRepo repo,
      @Nullable GithubIssueStatus oldStatus,
      GithubIssue issue,
      @Nullable GithubPullRequest pullRequest,
      Instant now)
      throws IOException {
    var data = issue.parseData(objectMapper);
    GithubPullRequest.Data pullRequestData = null;
    if (pullRequest != null) {
      pullRequestData = pullRequest.parseData(objectMapper);
    }
    Status newStatus = newStatus(repo, data, pullRequestData);
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

    var actionOwners = findActionOwner(repo, issue, data, pullRequestData, newStatus);
    return GithubIssueStatus.builder()
        .owner(issue.getOwner())
        .repo(issue.getRepo())
        .issueNumber(issue.getIssueNumber())
        .status(newStatus)
        .actionOwners(actionOwners)
        .updatedAt(data.getUpdatedAt())
        .expectedRespondAt(expectedRespondAt)
        .lastNotifiedAt(lastNotifiedAt)
        .nextNotifyAt(nextNotifyAt)
        .checkedAt(now)
        .build();
  }

  static Status newStatus(
      GithubRepo repo, GithubIssue.Data data, @Nullable GithubPullRequest.Data pullRequestData) {
    if (data.getState().equals("closed")) {
      return Status.CLOSED;
    }

    List<Label> labels = data.getLabels();

    if (hasMoreDataNeededLabel(labels)) {
      return Status.MORE_DATA_NEEDED;
    }

    if (pullRequestData != null && !pullRequestData.requestedReviewers().isEmpty()) {
      return Status.TRIAGED;
    }

    if (!data.getAssignees().isEmpty()) {
      return Status.TRIAGED;
    }

    if (!repo.isTeamLabelEnabled() || hasTeamLabel(labels)) {
      if (isTriaged(labels)) {
        return Status.TRIAGED;
      } else {
        return Status.REVIEWED;
      }
    }

    return Status.TO_BE_REVIEWED;
  }

  // TODO: More serious business days handling
  static @Nullable Instant getExpectedRespondAt(GithubIssue.Data data, Status status) {
    return switch (status) {
      case TO_BE_REVIEWED, MORE_DATA_NEEDED, REVIEWED -> data.getUpdatedAt().plus(7, DAYS);
      case TRIAGED -> getExpectedRespondAtForTriaged(data);
      default -> null;
    };
  }

  static @Nullable Instant getExpectedRespondAtForTriaged(GithubIssue.Data data) {
    List<Label> labels = data.getLabels();
    if (hasLabelPrefix(labels, "type: bug")) {
      if (hasLabelPrefix(labels, "P0")) {
        return data.getUpdatedAt().plus(1, DAYS);
      } else if (hasLabelPrefix(labels, "P1")) {
        return data.getUpdatedAt().plus(7, DAYS);
      } else if (hasLabelPrefix(labels, "P2")) {
        return data.getUpdatedAt().plus(120, DAYS);
      }
    }
    return null;
  }

  private ImmutableList<String> findActionOwner(
      GithubRepo repo,
      GithubIssue issue,
      GithubIssue.Data data,
      @Nullable GithubPullRequest.Data pullRequestData,
      Status status) {
    return switch (status) {
      case MORE_DATA_NEEDED -> ImmutableList.of(data.getUser().getLogin());
      case REVIEWED, TRIAGED -> findActionOwnerForReviewedOrTriaged(
          repo, issue, data, pullRequestData);
      default -> ImmutableList.of();
    };
  }

  private ImmutableList<String> findActionOwnerForReviewedOrTriaged(
      GithubRepo repo,
      GithubIssue issue,
      GithubIssue.Data data,
      @Nullable GithubPullRequest.Data pullRequestData) {

    if (pullRequestData != null) {
      if (!pullRequestData.requestedReviewers().isEmpty()) {
        return pullRequestData.requestedReviewers().stream()
            .map(User::getLogin)
            .collect(ImmutableList.toImmutableList());
      }
    }

    var assignees = data.getAssignees();
    if (!assignees.isEmpty()) {
      return assignees.stream().map(User::getLogin).collect(ImmutableList.toImmutableList());
    } else {
      List<Label> labels = data.getLabels();
      var teams =
          githubTeamService.findAll(issue.getOwner(), issue.getRepo()).stream()
              .filter(
                  team ->
                      labels.stream()
                          .anyMatch(label -> label.getName().equalsIgnoreCase(team.getLabel())))
              .toList();
      if (teams.isEmpty()) {
        if (repo.getActionOwner() != null) {
          return ImmutableList.of(repo.getActionOwner());
        } else {
          return ImmutableList.of();
        }
      }
      return teams.stream()
          .flatMap(team -> team.getTeamOwners().stream())
          .collect(ImmutableList.toImmutableList());
    }
  }

  private static boolean hasTeamLabel(List<Label> labels) {
    return hasLabelPrefix(labels, "team-");
  }

  private static boolean hasMoreDataNeededLabel(List<Label> labels) {
    return hasLabel(labels, "more data needed")
        || hasLabel(labels, "awaiting-user-response");
  }

  private static boolean isTriaged(List<Label> labels) {
    return hasLabel(labels, "P0")
        || hasLabel(labels, "P1")
        || hasLabel(labels, "P2")
        || hasLabel(labels, "P3")
        || hasLabel(labels, "P4")
        || hasLabel(labels, "awaiting-review")
        || hasLabel(labels, "awaiting-PR-merge");
  }

  private static boolean hasLabelPrefix(List<Label> labels, String prefix) {
    for (Label label : labels) {
      if (label.getName().toLowerCase().startsWith(prefix.toLowerCase())) {
        return true;
      }
    }

    return false;
  }

  private static boolean hasLabel(List<Label> labels, String name) {
    for (Label label : labels) {
      if (label.getName().equalsIgnoreCase(name)) {
        return true;
      }
    }

    return false;
  }
}
