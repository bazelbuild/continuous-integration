package build.bazel.dashboard.github.rest;

import build.bazel.dashboard.github.GithubTeamIssue;
import build.bazel.dashboard.github.GithubTeamService;
import io.reactivex.rxjava3.core.Flowable;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@Slf4j
public class GithubTeamRestController {
  private final GithubTeamService githubTeamService;

  @GetMapping("/github/{owner}/{repo}/teams/issues")
  public Flowable<GithubTeamIssue> listGithubTeamIssues(
      @PathVariable("owner") String owner, @PathVariable("repo") String repo) {
    return githubTeamService.listIssues(owner, repo);
  }
}
