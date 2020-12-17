package build.bazel.dashboard.github.db;

import build.bazel.dashboard.github.GithubIssueQueryCountTask;
import build.bazel.dashboard.github.GithubIssueQueryCountTaskResult;
import build.bazel.dashboard.utils.Period;
import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Observable;

import java.time.Instant;

public interface GithubIssueQueryCountTaskRepository {
  Observable<GithubIssueQueryCountTask> list(Period period);

  Completable saveResult(GithubIssueQueryCountTask task, Instant timestamp, int count);

  Observable<GithubIssueQueryCountTaskResult> listResult(
      String owner, String repo, String queryId, Period period, Instant from, Instant to);
}
