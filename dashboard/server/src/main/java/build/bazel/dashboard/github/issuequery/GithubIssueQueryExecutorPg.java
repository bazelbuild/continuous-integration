package build.bazel.dashboard.github.issuequery;

import build.bazel.dashboard.github.issuequery.GithubIssueQueryParser.Query;
import io.reactivex.rxjava3.core.Single;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.r2dbc.core.DatabaseClient;
import reactor.adapter.rxjava.RxJava3Adapter;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@RequiredArgsConstructor
public class GithubIssueQueryExecutorPg implements GithubIssueQueryExecutor {

  private final GithubIssueQueryParser queryParser;
  private final DatabaseClient databaseClient;

  @Override
  public Single<Integer> fetchQueryResultCount(String owner, String repo, String query) {
    Query parsedQuery = queryParser.parse(query);
    Map<String, Object> bindings = new HashMap<>();
    StringBuilder conditions = new StringBuilder();

    and(conditions, "owner = :owner");
    bindings.put("owner", owner);

    and(conditions, "repo = :repo");
    bindings.put("repo", repo);

    if (parsedQuery.getState() != null) {
      and(conditions, "state = :state");
      bindings.put("state", parsedQuery.getState());
    }

    if (parsedQuery.getIsPullRequest() != null) {
      and(conditions, "is_pull_request = :is_pull_request");
      bindings.put("is_pull_request", parsedQuery.getIsPullRequest());
    }

    if (!parsedQuery.getLabels().isEmpty()) {
      and(conditions, "labels @> :labels");
      bindings.put("labels", parsedQuery.getLabels().toArray(new String[0]));
    }

    if (!parsedQuery.getExcludeLabels().isEmpty()) {
      and(conditions, "NOT labels && :excluded_labels");
      bindings.put("excluded_labels", parsedQuery.getExcludeLabels().toArray(new String[0]));
    }

    StringBuilder sql = new StringBuilder("SELECT COUNT(*) AS count FROM github_issue");
    if (conditions.length() > 0) {
      sql.append(" WHERE ").append(conditions.toString());
    }

    DatabaseClient.GenericExecuteSpec spec = databaseClient.sql(sql.toString());

    for (Map.Entry<String, Object> entry : bindings.entrySet()) {
      spec = spec.bind(entry.getKey(), entry.getValue());
    }

    return RxJava3Adapter.monoToSingle(spec.map(row -> row.get("count", Integer.class)).one());
  }

  private void and(StringBuilder conditions, String condition) {
    if (conditions.length() > 0) {
      conditions.insert(0, "(");
      conditions.append(") AND ");
    }

    conditions.append(condition);
  }
}
