package build.bazel.dashboard.github.issue;

import lombok.Builder;
import lombok.Value;
import org.springframework.lang.Nullable;

/**
 * A value object representing the request message of List Repository Issues API.
 *
 * @see <a
 *     href="https://docs.github.com/en/free-pro-team@latest/rest/reference/issues#list-repository-issues">List
 *     repository issues</a>
 */
@Builder
@Value
public class ListRepositoryIssuesRequest {
  String owner;
  String repo;

  // TODO(coeuvre): Add more options

  // Results per page (max 100)
  int perPage;

  // Page number of the results to fetch.
  int page;
}
