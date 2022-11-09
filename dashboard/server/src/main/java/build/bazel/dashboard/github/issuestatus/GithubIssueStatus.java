package build.bazel.dashboard.github.issuestatus;

import com.google.common.collect.ImmutableList;
import lombok.Builder;
import lombok.Data;

import javax.annotation.Nullable;
import java.time.Instant;

@Builder
@Data
public class GithubIssueStatus {
  public enum Status {
    TO_BE_REVIEWED,
    MORE_DATA_NEEDED,
    REVIEWED,
    TRIAGED,
    CLOSED,
    DELETED,
  }

  String owner;
  String repo;
  int issueNumber;
  Status status;
  ImmutableList<String> actionOwners;
  Instant updatedAt;
  @Nullable Instant expectedRespondAt;
  @Nullable Instant lastNotifiedAt;
  @Nullable Instant nextNotifyAt;
  Instant checkedAt;
}
