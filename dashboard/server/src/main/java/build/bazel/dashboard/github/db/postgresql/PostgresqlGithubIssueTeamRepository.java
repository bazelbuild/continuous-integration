package build.bazel.dashboard.github.db.postgresql;

import build.bazel.dashboard.github.GithubIssueTeam;
import build.bazel.dashboard.github.db.GithubIssueTeamRepository;
import io.reactivex.rxjava3.core.Observable;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Component;
import reactor.adapter.rxjava.RxJava3Adapter;
import reactor.core.publisher.Flux;

import java.time.Instant;
import java.util.Optional;

@Component
@Slf4j
@RequiredArgsConstructor
public class PostgresqlGithubIssueTeamRepository implements GithubIssueTeamRepository {
  private final DatabaseClient databaseClient;

  @Override
  public Observable<GithubIssueTeam> list(String owner, String repo) {
    Flux<GithubIssueTeam> query =
        databaseClient
            .sql(
                "SELECT owner, repo, label, created_at, updated_at, name, team_owner FROM github_issue_team WHERE owner = :owner AND repo = :repo")
            .bind("owner", owner)
            .bind("repo", repo)
            .map(
                row ->
                    GithubIssueTeam.builder()
                        .owner(row.get("owner", String.class))
                        .repo(row.get("repo", String.class))
                        .label(row.get("label", String.class))
                        .createdAt(row.get("created_at", Instant.class))
                        .updatedAt(row.get("updated_at", Instant.class))
                        .name(row.get("name", String.class))
                        .teamOwner(Optional.ofNullable(row.get("team_owner", String.class)).orElse(""))
                        .build())
            .all();

    return RxJava3Adapter.fluxToObservable(query);
  }
}
