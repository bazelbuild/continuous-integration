package build.bazel.dashboard.github.issuequery;

import java.util.Optional;

public interface GithubIssueQueryRepo {
  Optional<GithubIssueQuery> findOne(String owner, String repo, String id);
}
