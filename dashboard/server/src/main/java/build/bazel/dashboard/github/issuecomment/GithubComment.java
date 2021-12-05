package build.bazel.dashboard.github.issuecomment;

import build.bazel.dashboard.github.issue.GithubIssue;
import com.fasterxml.jackson.databind.PropertyNamingStrategy;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Builder;
import lombok.Value;

@Builder
@Value
@JsonNaming(PropertyNamingStrategy.SnakeCaseStrategy.class)
public class GithubComment {
  long id;
  String body;
  GithubIssue.User user;
}
