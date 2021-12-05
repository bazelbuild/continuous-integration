package build.bazel.dashboard.github.sync.issue;

import build.bazel.dashboard.github.issue.GithubIssueService;
import build.bazel.dashboard.github.issuecomment.GithubIssueCommentService;
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

import javax.annotation.Nullable;
import java.time.Instant;

import static com.google.common.base.Preconditions.checkNotNull;

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
    return saveNewSyncIssueState(owner, repo, start, start + count, null);
  }

  @PutMapping("/internal/github/{owner}/{repo}/sync/issues/all")
  public Completable saveAllSyncIssueState(
      @PathVariable("owner") String owner, @PathVariable("repo") String repo) {
    return saveAllSyncIssueState(owner, repo, null);
  }

  private Completable saveNewSyncIssueState(
      String owner, String repo, Integer start, Integer end, @Nullable Instant lastTimestamp) {
    return jsonStateStore.save(
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

  private Completable saveAllSyncIssueState(
      String owner, String repo, @Nullable Instant lastTimestamp) {
    return githubIssueService
        .findMaxIssueNumber(owner, repo)
        .flatMapCompletable(
            maxIssueNumber ->
                saveNewSyncIssueState(owner, repo, 1, maxIssueNumber + 100, lastTimestamp));
  }

  @Scheduled(cron = "0 0 0 * * *", zone = "UTC")
  public void startNewSyncIfNotExisting() {
    githubRepoService
        .findAll()
        .flatMapCompletable(
            repo -> {
              String stateKey = buildSyncStateKey(repo.getOwner(), repo.getRepo());
              return jsonStateStore
                  .load(stateKey, SyncIssueState.class)
                  .flatMapCompletable(
                      jsonState -> {
                        if (jsonState.getData() != null) {
                          return Completable.complete();
                        }

                        return saveAllSyncIssueState(
                            repo.getOwner(), repo.getRepo(), jsonState.getTimestamp());
                      });
            },
            false,
            1)
        .blockingAwait();
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
            githubIssueCommentService.syncIssueComments(
                data.getOwner(), data.getRepo(), data.getCurrent()))
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
