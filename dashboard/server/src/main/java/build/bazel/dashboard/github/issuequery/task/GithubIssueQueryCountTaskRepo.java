package build.bazel.dashboard.github.issuequery.task;

import build.bazel.dashboard.utils.Period;
import com.google.common.collect.ImmutableList;
import java.time.Instant;

public interface GithubIssueQueryCountTaskRepo {
  ImmutableList<GithubIssueQueryCountTask> list(Period period);

  void saveResult(GithubIssueQueryCountTask task, Instant timestamp, int count);

  ImmutableList<GithubIssueQueryCountTaskResult> listResult(
      String owner, String repo, String queryId, Period period, Instant from, Instant to);
}
