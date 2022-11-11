package build.bazel.dashboard.github.repo;

import com.google.common.collect.ImmutableList;
import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Maybe;
import java.util.Optional;

public interface GithubRepoRepo {
  Optional<GithubRepo> findOne(String owner, String repo);

  ImmutableList<GithubRepo> findAll();
}
