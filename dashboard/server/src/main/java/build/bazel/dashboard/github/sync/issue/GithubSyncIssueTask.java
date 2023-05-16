package build.bazel.dashboard.github.sync.issue;

import static build.bazel.dashboard.utils.RxJavaVirtualThread.completable;
import static com.google.common.base.Preconditions.checkNotNull;

import build.bazel.dashboard.github.issue.GithubIssueService;
import build.bazel.dashboard.github.issuecomment.GithubIssueCommentService;
import build.bazel.dashboard.github.repo.GithubRepoService;
import build.bazel.dashboard.utils.JsonStateStore;
import build.bazel.dashboard.utils.JsonStateStore.JsonState;
import io.reactivex.rxjava3.core.Completable;
import java.time.Instant;
import javax.annotation.Nullable;
import lombok.Builder;
import lombok.RequiredArgsConstructor;
import lombok.Value;
import lombok.With;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@Slf4j
public class GithubSyncIssueTask {
  private final GithubRepoService githubRepoService;
  private final GithubIssueService githubIssueService;
  private final GithubIssueCommentService githubIssueCommentService;
  private final JsonStateStore jsonStateStore;

  @Builder
  @Value
  static class SyncIssueState {
    String owner;
    String repo;
    int start;
    @With int current;
    int end;
  }

  @PutMapping("/internal/github/{owner}/{repo}/sync/issues")
  public Completable saveNewSyncIssueState(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @RequestParam(name = "start") Integer start,
      @RequestParam(name = "count") Integer count) {
    return completable(() -> saveNewSyncIssueState(owner, repo, start, start + count, null));
  }

  @PutMapping("/internal/github/{owner}/{repo}/sync/issues/all")
  public Completable saveAllSyncIssueState(
      @PathVariable("owner") String owner, @PathVariable("repo") String repo) {
    return completable(() -> saveAllSyncIssueState(owner, repo, null));
  }

  private void saveNewSyncIssueState(
      String owner, String repo, Integer start, Integer end, @Nullable Instant lastTimestamp) {
    jsonStateStore.save(
        buildSyncStateKey(owner, repo),
        lastTimestamp,
        SyncIssueState.builder()
            .owner(owner)
            .repo(repo)
            .start(start)
            .current(start)
            .end(end)
            .build());
  }

  private void saveAllSyncIssueState(String owner, String repo, @Nullable Instant lastTimestamp) {
    var maxIssueNumber = githubIssueService.findMaxIssueNumber(owner, repo);
    saveNewSyncIssueState(owner, repo, 1, maxIssueNumber + 100, lastTimestamp);
  }

  @Scheduled(cron = "0 0 0 * * *", zone = "UTC")
  public void startNewSyncIfNotExisting() {
    for (var repo : githubRepoService.findAll()) {
      String stateKey = buildSyncStateKey(repo.getOwner(), repo.getRepo());
      var jsonState = jsonStateStore.load(stateKey, SyncIssueState.class);
      if (jsonState.getData() != null) {
        return;
      }
      saveAllSyncIssueState(repo.getOwner(), repo.getRepo(), jsonState.getTimestamp());
    }
  }

  // We have a rate limit 5000/hour = 1.4/sec. Use a conservative rate 0.5/sec
  @Scheduled(fixedDelay = 2000)
  public void syncGithubIssues() throws Throwable {
    for (var repo : githubRepoService.findAll()) {
      var jsonState =
          jsonStateStore.load(
              buildSyncStateKey(repo.getOwner(), repo.getRepo()), SyncIssueState.class);
      if (jsonState.getData() != null) {
        this.syncGithubIssue(jsonState);
        return;
      }
    }
  }

  private void syncGithubIssue(JsonState<SyncIssueState> jsonState) throws Throwable {
    SyncIssueState data = jsonState.getData();
    checkNotNull(data);

    if (data.current >= data.end) {
      jsonStateStore.delete(jsonState.getKey(), jsonState.getTimestamp());
      return;
    }

    var result =
        githubIssueService.fetchAndSave(data.getOwner(), data.getRepo(), data.getCurrent());
    if (result.getError() != null) {
      throw result.getError();
    }

    githubIssueCommentService.syncIssueComments(data.getOwner(), data.getRepo(), data.getCurrent());
    jsonStateStore.save(
        jsonState.getKey(), jsonState.getTimestamp(), data.withCurrent(data.getCurrent() + 1));
  }

  private String buildSyncStateKey(String owner, String repo) {
    return String.format("sync-github-issues/%s/%s", owner, repo);
  }
}
