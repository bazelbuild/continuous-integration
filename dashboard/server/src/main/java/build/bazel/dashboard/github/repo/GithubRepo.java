package build.bazel.dashboard.github.repo;

import java.time.Instant;
import javax.annotation.Nullable;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class GithubRepo {
  String owner;
  String repo;
  Instant createdAt;
  Instant updatedAt;
  @Nullable String actionOwner;
  boolean isTeamLabelEnabled;
}
