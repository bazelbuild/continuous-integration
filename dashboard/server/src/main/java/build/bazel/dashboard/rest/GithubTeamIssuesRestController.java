package build.bazel.dashboard.rest;

import build.bazel.dashboard.github.issue.GithubTeamIssue;
import build.bazel.dashboard.github.issue.GithubTeamIssueProvider;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

@RestController
public class GithubTeamIssuesRestController {
  private final GithubTeamIssueProvider githubTeamIssueProvider;

  public GithubTeamIssuesRestController(GithubTeamIssueProvider githubTeamIssueProvider) {
    this.githubTeamIssueProvider = githubTeamIssueProvider;
  }

  @GetMapping("/github/teams/issues")
  public Flux<GithubTeamIssue> listGithubTeamIssues() {
    return githubTeamIssueProvider.list();
  }
}
