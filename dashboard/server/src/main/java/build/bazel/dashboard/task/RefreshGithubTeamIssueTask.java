package build.bazel.dashboard.task;

import build.bazel.dashboard.github.issue.GithubTeamIssueCrawler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class RefreshGithubTeamIssueTask {
  private static final Logger log = LoggerFactory.getLogger(RefreshGithubTeamIssueTask.class);

  private final GithubTeamIssueCrawler crawler;

  public RefreshGithubTeamIssueTask(GithubTeamIssueCrawler crawler) {
    this.crawler = crawler;
  }

  // Refresh after 1 minutes
  @Scheduled(initialDelay = 0, fixedDelay = 60000000)
  public void refresh() {
    log.info("Refreshing Github team issues...");
    crawler.list().blockLast();
  }
}
