package build.bazel.dashboard.github.issuequery.task;

import build.bazel.dashboard.utils.Period;
import lombok.Builder;
import lombok.Value;

import java.time.Instant;

@Builder
@Value
public class GithubIssueQueryCountTask {
  String owner;
  String repo;
  String queryId;
  Period period;
  Instant createdAt;
  String query;
}
