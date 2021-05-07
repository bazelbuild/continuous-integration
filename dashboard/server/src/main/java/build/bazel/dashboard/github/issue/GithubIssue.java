package build.bazel.dashboard.github.issue;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategy;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Builder;
import lombok.Value;

import javax.annotation.Nullable;
import java.time.Instant;
import java.util.List;

@Builder
@Value
public class GithubIssue {
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

  public Data parseData(ObjectMapper objectMapper) throws JsonProcessingException {
    return objectMapper.treeToValue(data, Data.class);
  }

  @Builder
  @Value
  @JsonNaming(PropertyNamingStrategy.SnakeCaseStrategy.class)
  public static class Data {
    int number;
    User user;
    String title;
    String state;
    List<Label> labels;
    @Nullable User assignee;
    Instant createdAt;
    Instant updatedAt;
  }

  @Builder
  @Value
  public static class User {
    String login;
    String avatarUrl;
  }

  @Builder
  @Value
  public static class Label {
    String name;
    String description;
    String color;
  }
}
