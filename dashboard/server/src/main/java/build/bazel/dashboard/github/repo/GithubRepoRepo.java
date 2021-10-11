package build.bazel.dashboard.github.repo;

import io.reactivex.rxjava3.core.Flowable;
import lombok.Builder;
import lombok.Value;

import java.time.Instant;

public interface GithubRepoRepo {
  @Builder
  @Value
  class GithubRepoData {
    String owner;
    String repo;
    Instant createdAt;
    Instant updatedAt;
  }

  Flowable<GithubRepoData> findAll();
}
