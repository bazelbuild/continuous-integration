package build.bazel.dashboard.github;

import build.bazel.dashboard.github.issue.GithubIssueFetcher;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.reactivex.rxjava3.core.Completable;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

@Component
@Slf4j
@RequiredArgsConstructor
public class GithubEventHandler {
  private final GithubIssueFetcher githubIssueFetcher;

  public Completable onGithubRepositoryEvent(String owner, String repo, ObjectNode event) {
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

  private Completable updateGithubIssue(String owner, String repo, int issueNumber) {
    return Completable.fromSingle(githubIssueFetcher.fetch(owner, repo, issueNumber));
  }
}
