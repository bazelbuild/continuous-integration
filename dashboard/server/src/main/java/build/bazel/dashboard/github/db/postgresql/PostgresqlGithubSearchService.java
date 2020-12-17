package build.bazel.dashboard.github.db.postgresql;

import build.bazel.dashboard.github.GithubSearchService;
import io.reactivex.rxjava3.core.Single;
import lombok.Builder;
import lombok.RequiredArgsConstructor;
import lombok.Value;
import lombok.extern.slf4j.Slf4j;
import org.springframework.r2dbc.core.DatabaseClient;
import reactor.adapter.rxjava.RxJava3Adapter;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@RequiredArgsConstructor
public class PostgresqlGithubSearchService implements GithubSearchService {

  private final DatabaseClient databaseClient;

  @Override
  public Single<Integer> fetchSearchResultCount(String owner, String repo, String query) {
    String state = null;
    Boolean is_pull_request = null;
    List<String> labels = new ArrayList<>();
    List<String> excludeLabels = new ArrayList<>();

    String str = skipLeadingSpace(query);
    while (str.length() > 0) {
      if (str.startsWith("is:open")) {
        state = "open";

        str = str.substring(7);
        str = skipLeadingSpace(str);
      } else if (str.startsWith("is:closed")) {
        state = "closed";

        str = str.substring(9);
        str = skipLeadingSpace(str);
      } else if (str.startsWith("is:issue")) {
        is_pull_request = false;

        str = str.substring(8);
        str = skipLeadingSpace(str);
      } else if (str.startsWith("is:pr")) {
        is_pull_request = true;

        str = str.substring(5);
        str = skipLeadingSpace(str);
      } else if (str.startsWith("label:")) {
        str = str.substring(6);

        ExtractLabelResult result = extractLabel(str);
        labels.add(result.getLabel());

        str = str.substring(result.getSkip());
        str = skipLeadingSpace(str);
      } else if (str.startsWith("-label:")) {
        str = str.substring(7);

        ExtractLabelResult result = extractLabel(str);
        excludeLabels.add(result.getLabel());

        str = str.substring(result.getSkip());
        str = skipLeadingSpace(str);
      } else {
        throw new IllegalArgumentException("Unable to handle query: " + query);
      }
    }

    Map<String, Object> bindings = new HashMap<>();
    StringBuilder conditions = new StringBuilder();
    if (state != null) {
      and(conditions, "state = :state");
      bindings.put("state", state);
    }

    if (is_pull_request != null) {
      and(conditions, "is_pull_request = :is_pull_request");
      bindings.put("is_pull_request", is_pull_request);
    }

    if (!labels.isEmpty()) {
      and(conditions, "labels @> :labels");
      bindings.put("labels", labels.toArray(new String[0]));
    }

    if (!excludeLabels.isEmpty()) {
      and(conditions, "NOT labels && :excluded_labels");
      bindings.put("excluded_labels", excludeLabels.toArray(new String[0]));
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

  private String skipLeadingSpace(String str) {
    while (str.length() > 0 && str.charAt(0) == ' ') {
      str = str.substring(1);
    }
    return str;
  }

  @Builder
  @Value
  static class ExtractLabelResult {
    String label;
    int skip;
  }

  private ExtractLabelResult extractLabel(String str) {
    int offset = 0;
    char stop = ' ';
    if (str.charAt(0) == '"') {
      stop = '"';
      offset = 1;
    }

    StringBuilder label = new StringBuilder();
    while (offset < str.length()) {
      char ch = str.charAt(offset);
      offset += 1;
      if (ch == stop) {
        break;
      }
      label.append(ch);
    }
    return ExtractLabelResult.builder()
        .label(label.toString())
        .skip(offset)
        .build();
  }
}
