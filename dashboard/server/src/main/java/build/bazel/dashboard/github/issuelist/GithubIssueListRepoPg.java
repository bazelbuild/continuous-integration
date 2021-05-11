package build.bazel.dashboard.github.issuelist;

import build.bazel.dashboard.github.issuelist.GithubIssueListService.ListParams;
import build.bazel.dashboard.github.issuestatus.GithubIssueStatus;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.r2dbc.postgresql.codec.Json;
import io.r2dbc.spi.Row;
import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Single;
import lombok.Builder;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.r2dbc.core.DatabaseClient.GenericExecuteSpec;
import org.springframework.stereotype.Repository;
import reactor.adapter.rxjava.RxJava3Adapter;

import java.io.IOException;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

import static java.util.Objects.requireNonNull;

@Repository
@RequiredArgsConstructor
public class GithubIssueListRepoPg implements GithubIssueListRepo {

  private final ObjectMapper objectMapper;
  private final DatabaseClient databaseClient;

  @Builder
  static class QuerySpec {
    String from;
    String where;
    String order;
    String limit;
    Map<String, Object> bindings;
  }

  private static QuerySpec buildQuerySpec(ListParams params) {
    String from =
        " FROM github_issue_status gis INNER JOIN github_issue gi ON (gi.owner, gi.repo,"
            + " gi.issue_number) = (gis.owner, gis.repo, gis.issue_number) INNER JOIN"
            + " github_issue_data gid ON (gid.owner, gid.repo, gid.issue_number) = (gi.owner,"
            + " gi.repo, gi.issue_number)";

    Map<String, Object> bindings = new HashMap<>();
    StringBuilder where = new StringBuilder();

    if (params.getOwner() != null) {
      where.append(" AND gis.owner = :owner");
      bindings.put("owner", params.getOwner());
    }

    if (params.getRepo() != null) {
      where.append(" AND gis.repo = :repo");
      bindings.put("repo", params.getRepo());
    }

    if (params.getIsPullRequest() != null) {
      where.append(" AND gi.is_pull_request = :is_pull_request");
      bindings.put("is_pull_request", params.getIsPullRequest());
    }

    if (params.getStatus() != null) {
      where.append(" AND gis.status = :status");
      bindings.put("status", params.getStatus().toString());
    }

    if (params.getActionOwner() != null) {
      where.append(" AND gis.action_owner = :action_owner");
      bindings.put("action_owner", params.getActionOwner());
    }

    if (params.getLabels() != null && !params.getLabels().isEmpty()) {
      where.append(" AND gi.labels @> :labels");
      bindings.put("labels", params.getLabels().toArray(new String[0]));
    }

    if (where.length() > 0) {
      // Remove heading AND
      where.delete(0, 4);
      where.insert(0, " WHERE");
    }

    String order = " ORDER BY gi.issue_number DESC";

    if (params.getSort() != null) {
      switch (params.getSort()) {
        case EXPECTED_RESPOND_AT_ASC:
          order = " ORDER BY gis.expected_respond_at ASC";
          break;
        case EXPECTED_RESPOND_AT_DESC:
          order = " ORDER BY gis.expected_respond_at DESC";
          break;
      }
    }

    int page = 1;
    if (params.getPage() != null) {
      page = params.getPage();
      if (page < 1) {
        page = 1;
      }
    }
    int pageSize = 10;
    int offset = (page - 1) * pageSize;
    String limit = " LIMIT 10 OFFSET " + offset;

    return QuerySpec.builder()
        .from(from)
        .where(where.toString())
        .order(order)
        .limit(limit)
        .bindings(bindings)
        .build();
  }

  @Override
  public Flowable<GithubIssueList.Item> find(ListParams params) {
    QuerySpec query = buildQuerySpec(params);

    String fields =
        "gid.owner, gid.repo, gid.issue_number, gis.status, gis.action_owner,"
            + " gis.expected_respond_at, gid.data";
    String sql = "SELECT " + fields + query.from + query.where + query.order + query.limit;

    GenericExecuteSpec spec = databaseClient.sql(sql);
    for (Map.Entry<String, Object> binding : query.bindings.entrySet()) {
      spec = spec.bind(binding.getKey(), binding.getValue());
    }

    return RxJava3Adapter.fluxToFlowable(spec.map(this::toGithubIssueListItem).all());
  }

  @Override
  public Single<Integer> count(ListParams params) {
    QuerySpec query = buildQuerySpec(params);

    String sql = "SELECT COUNT(*) as total" + query.from + query.where;
    GenericExecuteSpec spec = databaseClient.sql(sql);
    for (Map.Entry<String, Object> binding : query.bindings.entrySet()) {
      spec = spec.bind(binding.getKey(), binding.getValue());
    }

    return RxJava3Adapter.monoToSingle(spec.map(row -> row.get("total", Integer.class)).one());
  }

  private GithubIssueList.Item toGithubIssueListItem(Row row) {
    try {
      return GithubIssueList.Item.builder()
          .owner(requireNonNull(row.get("owner", String.class)))
          .repo(requireNonNull(row.get("repo", String.class)))
          .issueNumber(requireNonNull(row.get("issue_number", Integer.class)))
          .status(GithubIssueStatus.Status.valueOf(row.get("status", String.class)))
          .actionOwner(row.get("action_owner", String.class))
          .expectedRespondAt(row.get("expected_respond_at", Instant.class))
          .data(objectMapper.readTree((requireNonNull(row.get("data", Json.class))).asArray()))
          .build();
    } catch (IOException e) {
      throw new IllegalStateException(e);
    }
  }

  @Override
  public Flowable<String> findAllActionOwner(ListParams params) {
    QuerySpec query = buildQuerySpec(params);

    StringBuilder sql = new StringBuilder("SELECT DISTINCT gis.action_owner");
    sql.append(query.from);
    sql.append(query.where);
    if (query.where.isBlank()) {
      sql.append(" WHERE");
    } else {
      sql.append(" AND");
    }
    sql.append(" gis.action_owner IS NOT NULL");

    GenericExecuteSpec spec = databaseClient.sql(sql.toString());
    for (Map.Entry<String, Object> binding : query.bindings.entrySet()) {
      spec = spec.bind(binding.getKey(), binding.getValue());
    }

    return RxJava3Adapter.fluxToFlowable(
        spec.map(row -> requireNonNull(row.get("action_owner", String.class))).all());
  }
}
