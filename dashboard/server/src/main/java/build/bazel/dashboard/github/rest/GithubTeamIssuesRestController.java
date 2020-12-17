package build.bazel.dashboard.github.rest;

import build.bazel.dashboard.github.GithubTeamIssue;
import build.bazel.dashboard.github.GithubTeamIssueProvider;
import io.reactivex.rxjava3.core.Observable;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@Slf4j
public class GithubTeamIssuesRestController {
  private final GithubTeamIssueProvider githubTeamIssueProvider;

  @GetMapping("/github/{owner}/{repo}/teams/issues")
  public Observable<GithubTeamIssue> listGithubTeamIssues(
      @PathVariable("owner") String owner, @PathVariable("repo") String repo) {
    return githubTeamIssueProvider.list(owner, repo);
  }
}
