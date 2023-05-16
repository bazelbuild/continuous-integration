package build.bazel.dashboard.github.issuecomment;

import static build.bazel.dashboard.utils.RxJavaVirtualThread.completable;

import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Flowable;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@Slf4j
public class GithubIssueCommentRestController {
  private final GithubIssueCommentService githubIssueCommentService;

  @PutMapping("/internal/github/{owner}/{repo}/issues/{issueNumber}/comments")
  public Completable updateGithubIssueComment(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @PathVariable("issueNumber") Integer issueNumber) {
    return completable(() -> githubIssueCommentService.syncIssueComments(owner, repo, issueNumber));
  }

  @GetMapping("/internal/github/{owner}/{repo}/issues/{issueNumber}/comments")
  public Flowable<GithubComment> findIssueComments(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @PathVariable("issueNumber") Integer issueNumber) {
    return githubIssueCommentService.findIssueComments(owner, repo, issueNumber);
  }
}
