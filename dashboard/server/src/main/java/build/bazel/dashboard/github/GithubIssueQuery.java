package build.bazel.dashboard.github;

import lombok.Builder;
import lombok.Value;

import java.time.Instant;

@Builder
@Value
public class GithubIssueQuery {
  String owner;
  String repo;
  String id;
  Instant createdAt;
  Instant updatedAt;
  String name;
  String query;
}
