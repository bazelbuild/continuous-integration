package build.bazel.dashboard.github.issue;

import io.reactivex.rxjava3.core.Observable;

public interface GithubTeamIssueProvider {
  Observable<GithubTeamIssue> list();
}
