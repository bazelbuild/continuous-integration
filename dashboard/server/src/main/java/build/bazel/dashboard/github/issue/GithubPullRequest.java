package build.bazel.dashboard.github.issue;

import build.bazel.dashboard.github.issue.GithubIssue.User;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import java.time.Instant;
import java.util.List;

public record GithubPullRequest(
    String owner, String repo, int issueNumber, Instant timestamp, String etag, JsonNode data) {

  public static GithubPullRequest empty(
      String owner, String repo, int issueNumber, ObjectMapper objectMapper) {
    return new GithubPullRequest(
        owner, repo, issueNumber, Instant.EPOCH, "", objectMapper.createObjectNode());
  }

  public Data parseData(ObjectMapper objectMapper) throws JsonProcessingException {
    return objectMapper.treeToValue(data, Data.class);
  }

  @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
  public record Data(List<User> requestedReviewers) {}
}
