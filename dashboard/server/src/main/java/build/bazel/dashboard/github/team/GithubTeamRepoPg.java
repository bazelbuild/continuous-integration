package build.bazel.dashboard.github.team;

import static java.util.Objects.requireNonNull;

import com.google.common.collect.ImmutableList;
import io.r2dbc.spi.Row;
import io.reactivex.rxjava3.core.Flowable;
import java.time.Instant;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;
import reactor.adapter.rxjava.RxJava3Adapter;
import reactor.core.publisher.Flux;

@Repository
@RequiredArgsConstructor
public class GithubTeamRepoPg implements GithubTeamRepo {
  private final DatabaseClient databaseClient;

  @Override
  public Flowable<GithubTeam> list(String owner, String repo) {
    Flux<GithubTeam> query =
        databaseClient
            .sql(
                "SELECT owner, repo, label, created_at, updated_at, name, team_owner,"
                    + " more_team_owners FROM github_team WHERE owner = :owner AND repo = :repo")
            .bind("owner", owner)
            .bind("repo", repo)
            .map(this::toGithubTeam)
            .all();

    return RxJava3Adapter.fluxToFlowable(query);
  }

  private GithubTeam toGithubTeam(Row row) {
    ImmutableList.Builder<String> teamOwners = ImmutableList.builder();

    String teamOwner = row.get("team_owner", String.class);
    if (teamOwner != null) {
      teamOwners.add(teamOwner);
    }
    teamOwners.add(requireNonNull(row.get("more_team_owners", String[].class)));

    return GithubTeam.builder()
        .owner(row.get("owner", String.class))
        .repo(row.get("repo", String.class))
        .label(row.get("label", String.class))
        .createdAt(row.get("created_at", Instant.class))
        .updatedAt(row.get("updated_at", Instant.class))
        .name(row.get("name", String.class))
        .teamOwners(teamOwners.build())
        .build();
  }
}
