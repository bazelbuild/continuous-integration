package build.bazel.dashboard.github.issuelist;

import build.bazel.dashboard.github.issuelist.GithubIssueListService.ListParams;
import io.reactivex.rxjava3.core.Single;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.stream.Collectors;

@RestController
@Slf4j
@RequiredArgsConstructor
public class GithubIssueListRestController {
  private final GithubIssueListService githubIssueListService;

  @GetMapping("/github/{owner}/{repo}/issues")
  public Single<GithubIssueList> find(
      @PathVariable("owner") String owner, @PathVariable("repo") String repo, ListParams params) {
    return githubIssueListService.find(owner, repo, params);
  }

  @GetMapping("/github/{owner}/{repo}/issues/owners")
  public Single<List<String>> findAllActionOwners(
      @PathVariable("owner") String owner, @PathVariable("repo") String repo) {
    return githubIssueListService
        .findAllActionOwner(owner, repo)
        .filter(actionOwner -> !actionOwner.isBlank())
        .sorted()
        .collect(Collectors.toList());
  }
}
