package build.bazel.dashboard.github.repo;

import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class GithubRepo {
  String owner;
  String repo;
}
