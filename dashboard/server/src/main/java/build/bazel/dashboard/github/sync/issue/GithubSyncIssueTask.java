package build.bazel.dashboard.github.sync.issue;

import build.bazel.dashboard.github.issue.GithubIssueService;
import build.bazel.dashboard.github.repo.GithubRepoService;
import build.bazel.dashboard.utils.JsonStateStore;
import build.bazel.dashboard.utils.JsonStateStore.JsonState;
import io.reactivex.rxjava3.core.Completable;
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

import static com.google.common.base.Preconditions.checkNotNull;

@RestController
@RequiredArgsConstructor
@Slf4j
public class GithubSyncIssueTask {
  private final GithubRepoService githubRepoService;
  private final GithubIssueService githubIssueService;
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
    checkNotNull(start);
    checkNotNull(count);
    return jsonStateStore.save(
        buildSyncStateKey(owner, repo),
        null,
        SyncIssueState.builder()
            .owner(owner)
            .repo(repo)
            .start(start)
            .current(start)
            .end(start + count)
            .build());
  }

  // We have a rate limit 5000/hour = 1.4/sec. Use a conservative rate 0.5/sec
  @Scheduled(fixedDelay = 2000)
  public void syncGithubIssues() {
    githubRepoService
        .findAll()
        .flatMapSingle(
            repo ->
                jsonStateStore.load(
                    buildSyncStateKey(repo.getOwner(), repo.getRepo()), SyncIssueState.class),
            false,
            1)
        .takeUntil(jsonState -> jsonState.getData() != null)
        .filter(jsonState -> jsonState.getData() != null)
        .flatMapCompletable(this::syncGithubIssue)
        .blockingAwait();
  }

  private Completable syncGithubIssue(JsonState<SyncIssueState> jsonState) {
    SyncIssueState data = jsonState.getData();
    checkNotNull(data);

    if (data.current >= data.end) {
      return jsonStateStore.delete(jsonState.getKey(), jsonState.getTimestamp());
    }

    return githubIssueService
        .fetchAndSave(data.getOwner(), data.getRepo(), data.getCurrent())
        .flatMapCompletable(
            result -> {
              if (result.getError() != null) {
                return Completable.error(result.getError());
              }
              return Completable.complete();
            })
        .andThen(
            jsonStateStore.save(
                jsonState.getKey(),
                jsonState.getTimestamp(),
                data.withCurrent(data.getCurrent() + 1)));
  }

  private String buildSyncStateKey(String owner, String repo) {
    return String.format("sync-github-issues/%s/%s", owner, repo);
  }
}
