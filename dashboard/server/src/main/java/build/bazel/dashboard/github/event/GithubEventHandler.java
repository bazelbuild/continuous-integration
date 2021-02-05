package build.bazel.dashboard.github.event;

import build.bazel.dashboard.github.issue.GithubIssueService;
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

  public Completable onGithubRepositoryEvent(String owner, String repo, ObjectNode event) {
    log.debug("Repository event {}: {}", event.get("type"), event);

    String type = event.get("type").asText();
    switch (type) {
      case "IssuesEvent":
        return updateGithubIssue(
            owner, repo, event.get("payload").get("issue").get("number").asInt());
      case "PullRequestEvent":
        return updateGithubIssue(
            owner, repo, event.get("payload").get("pull_request").get("number").asInt());
      default:
        return Completable.complete();
    }
  }

  public Completable onGithubRepositoryIssueEvent(String owner, String repo, ObjectNode event) {
    log.debug("Issue event {}: {}", event.get("event"), event);

    JsonNode issue = event.get("issue");
    if (issue != null) {
      return updateGithubIssue(owner, repo, issue.get("number").asInt());
    } else {
      return Completable.complete();
    }
  }

  private Completable updateGithubIssue(String owner, String repo, int issueNumber) {
    return Completable.fromSingle(githubIssueService.fetchAndSave(owner, repo, issueNumber));
  }
}
