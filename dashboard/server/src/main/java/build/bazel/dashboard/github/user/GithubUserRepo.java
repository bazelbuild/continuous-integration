package build.bazel.dashboard.github.user;

import io.reactivex.rxjava3.core.Flowable;

public interface GithubUserRepo {
  Flowable<GithubUser> findAll();
}
