package build.bazel.dashboard.github.issuelist;

import build.bazel.dashboard.github.issuelist.GithubIssueListService.ListParams;
import com.google.common.collect.ImmutableList;
import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Single;
import java.util.List;

public interface GithubIssueListRepo {
  Flowable<GithubIssueList.Item> find(ListParams params);

  Single<Integer> count(ListParams params);

  ImmutableList<String> findAllActionOwner(ListParams params);

  ImmutableList<String> findAllLabels(ListParams params);
}
