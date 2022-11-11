package build.bazel.dashboard.github.issuestatus;

import java.util.Optional;

public interface GithubIssueStatusRepo {
  void save(GithubIssueStatus status);

  Optional<GithubIssueStatus> findOne(String owner, String repo, int issueNumber);
}
