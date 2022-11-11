package build.bazel.dashboard.github.sync.event;

import build.bazel.dashboard.github.issue.GithubIssueService;
import build.bazel.dashboard.github.issuecomment.GithubIssueCommentService;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.reactivex.rxjava3.core.Completable;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

@Component
@Slf4j
@RequiredArgsConstructor
public class GithubEventHandler {
  private final GithubIssueService githubIssueService;
  private final GithubIssueCommentService githubIssueCommentService;

  public void onGithubRepositoryEvent(String owner, String repo, ObjectNode event) {
    log.debug("Repository event {}: {}", event.get("type"), event);

    String type = event.get("type").asText();
    switch (type) {
      case "IssueCommentEvent":
      case "IssuesEvent":
        updateGithubIssue(
            owner, repo, event.get("payload").get("issue").get("number").asInt());

      case "PullRequestReviewEvent":
      case "PullRequestReviewCommentEvent":
      case "PullRequestEvent":
        updateGithubIssue(
            owner, repo, event.get("payload").get("pull_request").get("number").asInt());

      default:
    }
  }

  public void onGithubRepositoryIssueEvent(String owner, String repo, ObjectNode event) {
    log.debug("Issue event {}: {}", event.get("event"), event);

    JsonNode issue = event.get("issue");
    if (issue != null) {
      updateGithubIssue(owner, repo, issue.get("number").asInt());
    }
  }

  private void updateGithubIssue(String owner, String repo, int issueNumber) {
    githubIssueService.fetchAndSave(owner, repo, issueNumber);
    githubIssueCommentService.syncIssueComments(owner, repo, issueNumber);
  }
}
