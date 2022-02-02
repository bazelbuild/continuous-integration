package build.bazel.dashboard.github.repo;

import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Maybe;

public interface GithubRepoRepo {
  Maybe<GithubRepo> findOne(String owner, String repo);

  Flowable<GithubRepo> findAll();
}
