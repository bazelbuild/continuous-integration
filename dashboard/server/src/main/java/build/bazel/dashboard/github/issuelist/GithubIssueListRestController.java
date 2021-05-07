package build.bazel.dashboard.github.issuelist;

import io.reactivex.rxjava3.core.Single;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Slf4j
@RequiredArgsConstructor
public class GithubIssueListRestController {
  private final GithubIssueListService githubIssueListService;

  @GetMapping("/github/{owner}/{repo}/issues")
  public Single<GithubIssueList> find(
      @PathVariable("owner") String owner, @PathVariable("repo") String repo) {
    return githubIssueListService.find(owner, repo);
  }
}
