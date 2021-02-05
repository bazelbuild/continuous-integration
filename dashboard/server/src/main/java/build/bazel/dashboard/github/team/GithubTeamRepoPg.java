package build.bazel.dashboard.github.team;

import io.reactivex.rxjava3.core.Flowable;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;
import reactor.adapter.rxjava.RxJava3Adapter;
import reactor.core.publisher.Flux;

import java.time.Instant;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class GithubTeamRepoPg implements GithubTeamRepo {
  private final DatabaseClient databaseClient;

  @Override
  public Flowable<GithubTeam> list(String owner, String repo) {
    Flux<GithubTeam> query =
        databaseClient
            .sql(
                "SELECT owner, repo, label, created_at, updated_at, name, team_owner FROM github_issue_team WHERE owner = :owner AND repo = :repo")
            .bind("owner", owner)
            .bind("repo", repo)
            .map(
                row ->
                    GithubTeam.builder()
                        .owner(row.get("owner", String.class))
                        .repo(row.get("repo", String.class))
                        .label(row.get("label", String.class))
                        .createdAt(row.get("created_at", Instant.class))
                        .updatedAt(row.get("updated_at", Instant.class))
                        .name(row.get("name", String.class))
                        .teamOwner(Optional.ofNullable(row.get("team_owner", String.class)).orElse(""))
                        .build())
            .all();

    return RxJava3Adapter.fluxToFlowable(query);
  }
}
