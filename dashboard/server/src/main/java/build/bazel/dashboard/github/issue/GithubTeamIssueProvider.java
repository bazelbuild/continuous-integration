package build.bazel.dashboard.github.issue;

import reactor.core.publisher.Flux;

public interface GithubTeamIssueProvider {
    Flux<GithubTeamIssue> list();
}
