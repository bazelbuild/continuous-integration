package build.bazel.dashboard.github.issuequery.task;

import build.bazel.dashboard.github.issuequery.GithubIssueQueryExecutor;
import build.bazel.dashboard.utils.Period;
import io.reactivex.rxjava3.core.Completable;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;

@RestController
@Slf4j
@RequiredArgsConstructor
public class CountGithubIssueQueryTask {
  private final GithubIssueQueryCountTaskRepo githubIssueQueryCountTaskRepo;
  private final GithubIssueQueryExecutor githubIssueQueryExecutor;

  @Scheduled(cron = "0 0 0 * * *", zone = "UTC")
  public void countDaily() {
    startCountDaily().blockingAwait();
  }

  @PutMapping("/github/search/count/daily")
  public Completable startCountDaily() {
    log.info("Counting Github daily issue queries at {}...", Instant.now());
    return githubIssueQueryCountTaskRepo
        .list(Period.DAILY)
        .flatMapCompletable(
            task ->
                githubIssueQueryExecutor
                    .fetchQueryResultCount(task.getOwner(), task.getRepo(), task.getQuery())
                    .flatMapCompletable(
                        count ->
                            githubIssueQueryCountTaskRepo.saveResult(
                                task, Instant.now(), count)),
            false,
            1);
  }
}
