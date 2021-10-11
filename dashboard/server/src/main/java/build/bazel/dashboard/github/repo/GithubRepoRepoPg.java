package build.bazel.dashboard.github.repo;

import io.reactivex.rxjava3.core.Flowable;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;
import reactor.adapter.rxjava.RxJava3Adapter;
import reactor.core.publisher.Flux;

import java.time.Instant;

@Repository
@RequiredArgsConstructor
public class GithubRepoRepoPg implements GithubRepoRepo {

  private final DatabaseClient databaseClient;

  @Override
  public Flowable<GithubRepoData> findAll() {
    Flux<GithubRepoData> query =
        databaseClient
            .sql("SELECT owner, repo, created_at, updated_at FROM github_repo")
            .map(row -> GithubRepoData.builder()
                .owner(row.get("owner", String.class))
                .repo(row.get("repo", String.class))
                .createdAt(row.get("created_at", Instant.class))
                .updatedAt(row.get("updated_at", Instant.class))
                .build())
            .all();
    return RxJava3Adapter.fluxToFlowable(query);
  }
}
