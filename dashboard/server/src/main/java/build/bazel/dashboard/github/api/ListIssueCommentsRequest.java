package build.bazel.dashboard.github.api;

import javax.annotation.Nullable;
import lombok.Builder;
import lombok.Value;

@Builder
@Value
public class ListIssueCommentsRequest {
  String owner;
  String repo;
  int issueNumber;
  Integer perPage;
  Integer page;
  @Nullable String etag;
}
