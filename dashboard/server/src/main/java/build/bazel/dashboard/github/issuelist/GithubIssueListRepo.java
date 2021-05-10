package build.bazel.dashboard.github.issuelist;

import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Single;

public interface GithubIssueListRepo {
  Flowable<GithubIssueList.Item> find(String owner, String repo, GithubIssueListService.ListParams params);

  Single<Integer> count(String owner, String repo, GithubIssueListService.ListParams params);

  Flowable<String> findAllActionOwner(String owner, String repo);
}
