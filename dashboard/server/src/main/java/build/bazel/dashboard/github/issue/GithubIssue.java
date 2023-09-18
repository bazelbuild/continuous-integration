package build.bazel.dashboard.github.issue;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.List;
import javax.annotation.Nullable;
import lombok.Builder;
import lombok.Value;

@Builder
@Value
public class GithubIssue {
  String owner;
  String repo;
  int issueNumber;
  Instant timestamp;
  String etag;
  JsonNode data;

  public static GithubIssue empty(
      String owner, String repo, int issueNumber, ObjectMapper objectMapper) {
    return GithubIssue.builder()
        .owner(owner)
        .repo(repo)
        .issueNumber(issueNumber)
        .timestamp(Instant.EPOCH)
        .etag("")
        .data(objectMapper.createObjectNode())
        .build();
  }

  public static Data parseData(ObjectMapper objectMapper, JsonNode data) throws JsonProcessingException {
    return objectMapper.treeToValue(data, Data.class);
  }

  public Data parseData(ObjectMapper objectMapper) throws JsonProcessingException {
    return parseData(objectMapper, data);
  }

  @Builder
  @Value
  @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
  public static class Data {
    int number;
    User user;
    String title;
    String state;
    List<Label> labels;
    List<User> assignees;
    Instant createdAt;
    Instant updatedAt;
    @Nullable JsonNode pullRequest;

    public boolean isPullRequest() {
      return pullRequest != null;
    }
  }

  @Builder
  @Value
  @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
  public static class User {
    String login;
    String avatarUrl;
  }

  @Builder
  @Value
  @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
  public static class Label {
    String name;
    String description;
    String color;
  }
}
