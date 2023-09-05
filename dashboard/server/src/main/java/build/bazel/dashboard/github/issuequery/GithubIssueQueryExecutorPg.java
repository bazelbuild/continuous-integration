package build.bazel.dashboard.github.issuequery;

import build.bazel.dashboard.github.issuequery.GithubIssueQueryParser.Query;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.common.collect.ImmutableList;
import io.r2dbc.postgresql.codec.Json;
import io.r2dbc.postgresql.codec.PostgresqlObjectId;
import io.r2dbc.spi.Parameters;
import lombok.Builder;
import lombok.RequiredArgsConstructor;
import lombok.Value;
import lombok.extern.slf4j.Slf4j;
import org.springframework.r2dbc.core.DatabaseClient;
import reactor.adapter.rxjava.RxJava3Adapter;
import reactor.core.publisher.Flux;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

import static com.google.common.collect.ImmutableList.toImmutableList;
import static java.util.Objects.requireNonNull;

@Slf4j
@RequiredArgsConstructor
public class GithubIssueQueryExecutorPg implements GithubIssueQueryExecutor {

  private final ObjectMapper objectMapper;
  private final GithubIssueQueryParser queryParser;
  private final DatabaseClient databaseClient;

  @Override
  public QueryResult execute(String owner, String repo, String query) {
    var items = fetchQueryResult(owner, repo, query);
    var count = fetchQueryResultCount(owner, repo, query);
    return QueryResult.builder().totalCount(count).items(items).build();
  }

  private ImmutableList<JsonNode> fetchQueryResult(String owner, String repo, String query) {
    SqlCondition condition = buildSqlCondition(owner, repo, query);
    StringBuilder sql =
        new StringBuilder(
            "SELECT data FROM github_issue_data WHERE (owner, repo, issue_number) IN "
                + "(SELECT owner, repo, issue_number FROM github_issue");
    if (condition.condition.length() > 0) {
      sql.append(" WHERE ").append(condition.condition);
    }
    sql.append(")");

    DatabaseClient.GenericExecuteSpec spec = databaseClient.sql(sql.toString());

    for (Map.Entry<String, Object> entry : condition.bindings.entrySet()) {
      spec = spec.bind(entry.getKey(), entry.getValue());
    }

    return spec.map(
            row -> {
              try {
                return objectMapper.readTree(
                    (requireNonNull(row.get("data", Json.class))).asArray());
              } catch (IOException e) {
                throw new IllegalStateException(e);
              }
            })
        .all()
        .collect(toImmutableList())
        .block();
  }

  @Override
  public Integer fetchQueryResultCount(String owner, String repo, String query) {
    SqlCondition condition = buildSqlCondition(owner, repo, query);
    StringBuilder sql = new StringBuilder("SELECT COUNT(*) AS count FROM github_issue");
    if (condition.condition.length() > 0) {
      sql.append(" WHERE ").append(condition.condition);
    }

    DatabaseClient.GenericExecuteSpec spec = databaseClient.sql(sql.toString());

    for (Map.Entry<String, Object> entry : condition.bindings.entrySet()) {
      spec = spec.bind(entry.getKey(), entry.getValue());
    }

    return spec.map(row -> row.get("count", Integer.class)).one().block();
  }

  private void and(StringBuilder conditions, String condition) {
    if (conditions.length() > 0) {
      conditions.insert(0, "(");
      conditions.append(") AND ");
    }

    conditions.append(condition);
  }

  @Builder
  @Value
  static class SqlCondition {
    String condition;
    Map<String, Object> bindings;
  }

  private SqlCondition buildSqlCondition(String owner, String repo, String query) {
    Query parsedQuery = queryParser.parse(query);
    Map<String, Object> bindings = new HashMap<>();
    StringBuilder condition = new StringBuilder();

    and(condition, "owner = :owner");
    bindings.put("owner", owner);

    and(condition, "repo = :repo");
    bindings.put("repo", repo);

    if (parsedQuery.getState() != null) {
      and(condition, "state = :state");
      bindings.put("state", parsedQuery.getState());
    }

    if (parsedQuery.getIsPullRequest() != null) {
      and(condition, "is_pull_request = :is_pull_request");
      bindings.put("is_pull_request", parsedQuery.getIsPullRequest());
    }

    if (parsedQuery.getNoMilestone() != null && parsedQuery.getNoMilestone()) {
      and(condition, "milestone = ''");
    }

    if (!parsedQuery.getLabels().isEmpty()) {
      and(condition, "labels @> :labels");
      bindings.put(
          "labels",
          Parameters.in(
              PostgresqlObjectId.UNSPECIFIED, parsedQuery.getLabels().toArray(new String[0])));
    }

    if (!parsedQuery.getExcludeLabels().isEmpty()) {
      and(condition, "NOT labels && :excluded_labels");
      bindings.put(
          "excluded_labels",
          Parameters.in(
              PostgresqlObjectId.UNSPECIFIED,
              parsedQuery.getExcludeLabels().toArray(new String[0])));
    }

    return SqlCondition.builder().condition(condition.toString()).bindings(bindings).build();
  }
}
