package build.bazel.dashboard.github.issuequery;

import lombok.Builder;
import lombok.RequiredArgsConstructor;
import lombok.Value;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.annotation.Nullable;
import java.util.ArrayList;
import java.util.List;

@Component
@Slf4j
@RequiredArgsConstructor
public class GithubIssueQueryParser {
  @Builder
  @Value
  public static class Query {
    @Nullable
    String state;
    @Nullable
    Boolean isPullRequest;
    List<String> labels;
    List<String> excludeLabels;
  }

  public Query parse(String query) {
    String state = null;
    Boolean isPullRequest = null;
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
        isPullRequest = false;

        str = str.substring(8);
        str = skipLeadingSpace(str);
      } else if (str.startsWith("is:pr")) {
        isPullRequest = true;

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

    return Query.builder()
        .state(state)
        .isPullRequest(isPullRequest)
        .labels(labels)
        .excludeLabels(excludeLabels)
        .build();
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
