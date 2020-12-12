package build.bazel.dashboard.github.issue.task;

import build.bazel.dashboard.github.issue.GithubTeamIssueCrawler;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
@Slf4j
@RequiredArgsConstructor
public class RefreshGithubTeamIssueTask {
  private final GithubTeamIssueCrawler crawler;

  // Refresh after 1 minutes
  @Scheduled(initialDelay = 0, fixedDelay = 60000)
  public void refresh() {
    log.info("Refreshing Github team issues...");
    crawler.list().blockLast();
  }
}
