package build.bazel.dashboard.github.issuelist;

import build.bazel.dashboard.github.issuelist.GithubIssueListService.ListParams;
import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Single;

public interface GithubIssueListRepo {
  Flowable<GithubIssueList.Item> find(ListParams params);

  Single<Integer> count(ListParams params);

  Flowable<String> findAllActionOwner(ListParams params);
}
