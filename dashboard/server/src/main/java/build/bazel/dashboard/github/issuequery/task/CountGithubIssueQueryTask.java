package build.bazel.dashboard.github.issuequery.task;

import static build.bazel.dashboard.utils.RxJavaVirtualThread.completable;

import build.bazel.dashboard.github.issuequery.GithubIssueQueryExecutor;
import build.bazel.dashboard.utils.Period;
import io.reactivex.rxjava3.core.Completable;
import java.time.Instant;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RestController;

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

  @PutMapping("/internal/github/search/count/daily")
  public Completable startCountDaily() {
    return completable(
        () -> {
          log.info("Counting Github daily issue queries at {}...", Instant.now());
          var tasks = githubIssueQueryCountTaskRepo.list(Period.DAILY);
          for (var task : tasks) {
            var count =
                githubIssueQueryExecutor.fetchQueryResultCount(
                    task.getOwner(), task.getRepo(), task.getQuery());
            githubIssueQueryCountTaskRepo.saveResult(task, Instant.now(), count);
          }
        });
  }
}
