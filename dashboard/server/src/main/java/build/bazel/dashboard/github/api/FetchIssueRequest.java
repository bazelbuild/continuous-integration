package build.bazel.dashboard.github.api;

import lombok.Builder;
import lombok.Value;

@Builder
@Value
public class FetchIssueRequest {
  String owner;
  String repo;
  int issueNumber;
  String etag;
}
