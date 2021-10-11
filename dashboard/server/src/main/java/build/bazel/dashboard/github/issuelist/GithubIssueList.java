package build.bazel.dashboard.github.issuelist;

import build.bazel.dashboard.github.issuestatus.GithubIssueStatus;
import com.fasterxml.jackson.databind.JsonNode;
import lombok.Builder;
import lombok.Value;

import javax.annotation.Nullable;
import java.time.Instant;
import java.util.List;

@Builder
@Value
public class GithubIssueList {
  List<Item> items;
  int total;
  int page;
  int pageSize;

  @Builder
  @Value
  public static class Item {
    String owner;
    String repo;
    int issueNumber;
    GithubIssueStatus.Status status;
    @Nullable String actionOwner;
    @Nullable Instant expectedRespondAt;
    JsonNode data;
  }
}
