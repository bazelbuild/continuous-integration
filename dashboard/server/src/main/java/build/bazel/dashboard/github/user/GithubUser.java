package build.bazel.dashboard.github.user;

import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class GithubUser {
  String username;
  String email;
}
