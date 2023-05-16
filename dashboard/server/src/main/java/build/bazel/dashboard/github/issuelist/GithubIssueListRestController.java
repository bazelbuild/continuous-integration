package build.bazel.dashboard.github.issuelist;

import static build.bazel.dashboard.utils.RxJavaVirtualThread.single;
import static com.google.common.collect.ImmutableList.toImmutableList;

import build.bazel.dashboard.github.issuelist.GithubIssueListService.ListParams;
import io.reactivex.rxjava3.core.Single;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

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
    return single(
        () ->
            githubIssueListService.findAllActionOwner(params).stream()
                .filter(actionOwner -> !actionOwner.isBlank())
                .sorted()
                .collect(toImmutableList()));
  }

  @GetMapping("/github/issues/labels")
  public Single<List<String>> findAllLabels(ListParams params) {
    return single(
        () ->
            githubIssueListService.findAllLabels(params).stream()
                .filter(label -> !label.isBlank())
                .sorted()
                .collect(toImmutableList()));
  }
}
