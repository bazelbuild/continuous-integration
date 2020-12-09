package build.bazel.dashboard.github.issue;

import com.fasterxml.jackson.databind.JsonNode;
import reactor.core.publisher.Mono;

public interface GithubIssuesApi {
  Mono<JsonNode> listRepositoryIssues(ListRepositoryIssuesRequest request);
}
