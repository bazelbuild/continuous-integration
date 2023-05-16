package build.bazel.dashboard.github.issuelist;

import static com.google.common.collect.ImmutableList.toImmutableList;
import static java.util.Objects.requireNonNull;

import build.bazel.dashboard.github.issuelist.GithubIssueListService.ListParams;
import build.bazel.dashboard.github.issuestatus.GithubIssueStatus;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.common.collect.ImmutableList;
import io.r2dbc.postgresql.codec.Json;
import io.r2dbc.spi.Readable;
import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Single;
import java.io.IOException;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import lombok.Builder;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.r2dbc.core.DatabaseClient.GenericExecuteSpec;
import org.springframework.stereotype.Repository;
import reactor.adapter.rxjava.RxJava3Adapter;

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
      where.append(
          " AND (gis.action_owner = :action_owner OR :action_owner = ANY(gis.more_action_owners))");
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

    int page = requireNonNull(params.getPage());
    int pageSize = requireNonNull(params.getPageSize());
    int offset = (page - 1) * pageSize;
    String limit = " LIMIT " + pageSize + " OFFSET " + offset;

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
            + " gis.more_action_owners, gis.expected_respond_at, gid.data";
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

  private GithubIssueList.Item toGithubIssueListItem(Readable row) {
    String actionOwner = row.get("action_owner", String.class);
    if (actionOwner == null) {
      String[] moreActionOwners = requireNonNull(row.get("more_action_owners", String[].class));
      if (moreActionOwners.length > 0) {
        actionOwner = moreActionOwners[0];
      }
    }

    try {
      return GithubIssueList.Item.builder()
          .owner(requireNonNull(row.get("owner", String.class)))
          .repo(requireNonNull(row.get("repo", String.class)))
          .issueNumber(requireNonNull(row.get("issue_number", Integer.class)))
          .status(GithubIssueStatus.Status.valueOf(row.get("status", String.class)))
          .actionOwner(actionOwner)
          .expectedRespondAt(row.get("expected_respond_at", Instant.class))
          .data(objectMapper.readTree((requireNonNull(row.get("data", Json.class))).asArray()))
          .build();
    } catch (IOException e) {
      throw new IllegalStateException(e);
    }
  }

  @Override
  public ImmutableList<String> findAllActionOwner(ListParams params) {
    if (params.getActionOwner() != null) {
      return ImmutableList.of(params.getActionOwner());
    }

    QuerySpec query = buildQuerySpec(params);

    StringBuilder sql =
        new StringBuilder(
            "SELECT DISTINCT unnest(array_append(gis.more_action_owners, gis.action_owner)) as"
                + " action_owner");
    sql.append(query.from);
    sql.append(query.where);

    GenericExecuteSpec spec = databaseClient.sql(sql.toString());
    for (Map.Entry<String, Object> binding : query.bindings.entrySet()) {
      spec = spec.bind(binding.getKey(), binding.getValue());
    }

    return spec.map(
            row -> {
              String actionOwner = row.get("action_owner", String.class);
              if (actionOwner == null) {
                actionOwner = "";
              }
              return actionOwner;
            })
        .all()
        .collect(toImmutableList())
        .block();
  }

  @Override
  public ImmutableList<String> findAllLabels(ListParams params) {
    QuerySpec query = buildQuerySpec(params);
    StringBuilder sql = new StringBuilder("SELECT DISTINCT unnest(gi.labels) AS label");
    sql.append(query.from);
    sql.append(query.where);

    GenericExecuteSpec spec = databaseClient.sql(sql.toString());
    for (Map.Entry<String, Object> binding : query.bindings.entrySet()) {
      spec = spec.bind(binding.getKey(), binding.getValue());
    }

    return spec.map(row -> requireNonNull(row.get("label", String.class)))
        .all()
        .collect(toImmutableList())
        .block();
  }
}
