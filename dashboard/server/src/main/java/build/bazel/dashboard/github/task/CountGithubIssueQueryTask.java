package build.bazel.dashboard.github.task;

import build.bazel.dashboard.github.GithubHistoricalSearchService;
import build.bazel.dashboard.github.GithubSearchService;
import build.bazel.dashboard.github.db.GithubIssueQueryCountTaskRepository;
import build.bazel.dashboard.utils.Period;
import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Single;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;

@RestController
@Slf4j
@RequiredArgsConstructor
public class CountGithubIssueQueryTask {
  private final GithubIssueQueryCountTaskRepository githubIssueQueryCountTaskRepository;
  private final GithubSearchService githubSearchService;
  private final GithubHistoricalSearchService githubHistoricalSearchService;

  @Scheduled(cron = "0 0 0 * * *", zone = "UTC")
  public void countDaily() {
    startCountDaily(null).blockingAwait();
  }

  @PutMapping("/github/search/count/daily")
  public Completable startCountDaily(
      @RequestParam(value = "timestamp", required = false) Instant timestamp) {
    log.info(
        "Counting Github daily issue queries at {}...",
        timestamp != null ? timestamp : Instant.now());
    return githubIssueQueryCountTaskRepository
        .list(Period.DAILY)
        .flatMapCompletable(
            task -> {
              Single<Integer> countSingle;

              if (timestamp == null) {
                countSingle =
                    githubSearchService.fetchSearchResultCount(
                        task.getOwner(), task.getRepo(), task.getQuery());
              } else {
                countSingle =
                    githubHistoricalSearchService.fetchSearchResultCount(
                        task.getOwner(), task.getRepo(), task.getQuery(), timestamp);
              }

              return countSingle.flatMapCompletable(
                  count ->
                      githubIssueQueryCountTaskRepository.saveResult(
                          task, timestamp != null ? timestamp : Instant.now(), count));
            },
            false,
            1);
  }
}
