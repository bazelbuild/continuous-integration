package build.bazel.dashboard.github.issue;

import com.fasterxml.jackson.databind.JsonNode;
import lombok.Builder;
import lombok.Value;

import java.time.Instant;

@Builder
@Value
public
class GithubIssue {
  String owner;
  String repo;
  int issueNumber;
  Instant timestamp;
  String etag;
  JsonNode data;

  public static GithubIssue empty(String owner, String repo, int issueNumber) {
    return GithubIssue.builder()
        .owner(owner)
        .repo(repo)
        .issueNumber(issueNumber)
        .timestamp(Instant.EPOCH)
        .etag("")
        .build();
  }
}
