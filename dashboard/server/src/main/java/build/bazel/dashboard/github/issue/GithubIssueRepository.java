package build.bazel.dashboard.github.issue;

import com.fasterxml.jackson.databind.JsonNode;
import lombok.Builder;
import lombok.Value;
import lombok.With;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Instant;

public interface GithubIssueRepository {

  @Builder
  @Value
  @With
  class GithubIssue {
    String owner;
    String repo;
    int issueNumber;
    Instant timestamp;
    String eTag;
    JsonNode data;

    public static GithubIssue empty(String owner, String repo, int issueNumber) {
      return GithubIssue.builder()
          .owner(owner)
          .repo(repo)
          .issueNumber(issueNumber)
          .timestamp(Instant.EPOCH)
          .eTag("")
          .build();
    }
  }

  Mono<GithubIssue> save(GithubIssue githubIssue);

  Mono<GithubIssue> findOne(String owner, String repo, int issueNumber);

  Flux<GithubIssue> list();
}
