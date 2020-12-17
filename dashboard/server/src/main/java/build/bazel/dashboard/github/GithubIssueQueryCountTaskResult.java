package build.bazel.dashboard.github;

import build.bazel.dashboard.utils.Period;
import lombok.Builder;
import lombok.Value;

import java.time.Instant;

@Builder
@Value
public class GithubIssueQueryCountTaskResult {
  String owner;
  String repo;
  String queryId;
  Period period;
  Instant timestamp;
  Integer count;
}
