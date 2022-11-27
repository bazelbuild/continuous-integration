package build.bazel.dashboard.github.issuecomment;

import build.bazel.dashboard.github.issue.GithubIssue;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Builder;
import lombok.Value;

@Builder
@Value
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class GithubComment {
  long id;
  String body;
  GithubIssue.User user;
}
