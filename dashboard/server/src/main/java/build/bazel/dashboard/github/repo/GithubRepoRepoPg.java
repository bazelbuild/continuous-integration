package build.bazel.dashboard.github.repo;

import static java.util.Objects.requireNonNull;

import io.r2dbc.spi.Row;
import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Maybe;
import java.time.Instant;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;
import reactor.adapter.rxjava.RxJava3Adapter;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@Repository
@RequiredArgsConstructor
public class GithubRepoRepoPg implements GithubRepoRepo {

  private final DatabaseClient databaseClient;

  @Override
  public Maybe<GithubRepo> findOne(String owner, String repo) {
    Mono<GithubRepo> query =
        databaseClient
            .sql(
                "SELECT owner, repo, created_at, updated_at, action_owner, is_team_label_enabled"
                    + " FROM github_repo WHERE owner = :owner AND repo = :repo")
            .bind("owner", owner)
            .bind("repo", repo)
            .map(this::toGithubRepo)
            .one();
    return RxJava3Adapter.monoToMaybe(query);
  }

  @Override
  public Flowable<GithubRepo> findAll() {
    Flux<GithubRepo> query =
        databaseClient
            .sql(
                "SELECT owner, repo, created_at, updated_at, action_owner, is_team_label_enabled"
                    + " FROM github_repo")
            .map(this::toGithubRepo)
            .all();
    return RxJava3Adapter.fluxToFlowable(query);
  }

  private GithubRepo toGithubRepo(Row row) {
    return GithubRepo.builder()
        .owner(requireNonNull(row.get("owner", String.class)))
        .repo(requireNonNull(row.get("repo", String.class)))
        .createdAt(requireNonNull(row.get("created_at", Instant.class)))
        .updatedAt(requireNonNull(row.get("updated_at", Instant.class)))
        .actionOwner(row.get("action_owner", String.class))
        .isTeamLabelEnabled(requireNonNull(row.get("is_team_label_enabled", Boolean.class)))
        .build();
  }
}
