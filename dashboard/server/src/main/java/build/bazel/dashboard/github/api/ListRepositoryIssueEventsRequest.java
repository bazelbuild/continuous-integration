package build.bazel.dashboard.github.api;

import lombok.Builder;
import lombok.Value;

@Builder
@Value
public class ListRepositoryIssueEventsRequest {
  String owner;
  String repo;
  Integer perPage;
  Integer page;
  String etag;
}
