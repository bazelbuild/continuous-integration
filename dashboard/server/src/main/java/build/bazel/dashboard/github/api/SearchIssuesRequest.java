package build.bazel.dashboard.github.api;

import lombok.Builder;
import lombok.Value;

@Builder
@Value
public class SearchIssuesRequest {
  String q;
  String sort;
  String order;
  Integer perPage;
  Integer page;
}
