package build.bazel.dashboard.github.issuelist;

import build.bazel.dashboard.github.issuelist.GithubIssueListService.ListParams;
import io.reactivex.rxjava3.core.Single;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.stream.Collectors;

@RestController
@Slf4j
@RequiredArgsConstructor
public class GithubIssueListRestController {
  private final GithubIssueListService githubIssueListService;

  @GetMapping("/github/issues")
  public Single<GithubIssueList> find(ListParams params) {
    return githubIssueListService.find(params);
  }

  @GetMapping("/github/issues/owners")
  public Single<List<String>> findAllActionOwners(ListParams params) {
    return githubIssueListService
        .findAllActionOwner(params)
        .filter(actionOwner -> !actionOwner.isBlank())
        .sorted()
        .collect(Collectors.toList());
  }
}
