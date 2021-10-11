package build.bazel.dashboard.github.issuequery;

import com.fasterxml.jackson.databind.JsonNode;
import io.reactivex.rxjava3.core.Single;
import lombok.Builder;
import lombok.Value;

import java.util.List;

public interface GithubIssueQueryExecutor {
  @Builder
  @Value
  class QueryResult {
    List<JsonNode> items;
    int totalCount;
  }

  Single<QueryResult> execute(String owner, String repo, String query);

  default Single<Integer> fetchQueryResultCount(String owner, String repo, String query) {
    return execute(owner, repo, query).map(result -> result.totalCount);
  }
}
