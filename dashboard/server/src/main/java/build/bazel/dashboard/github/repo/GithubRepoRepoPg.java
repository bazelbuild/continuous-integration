package build.bazel.dashboard.github.repo;

import static com.google.common.collect.ImmutableList.toImmutableList;
import static java.util.Objects.requireNonNull;

import com.google.common.collect.ImmutableList;
import io.r2dbc.spi.Readable;
import java.time.Instant;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class GithubRepoRepoPg implements GithubRepoRepo {

  private final DatabaseClient databaseClient;

  @Override
  public Optional<GithubRepo> findOne(String owner, String repo) {
    return Optional.ofNullable(
        databaseClient
            .sql(
                "SELECT owner, repo, created_at, updated_at, action_owner, is_team_label_enabled"
                    + " FROM github_repo WHERE owner = :owner AND repo = :repo")
            .bind("owner", owner)
            .bind("repo", repo)
            .map(this::toGithubRepo)
            .one()
            .block());
  }

  @Override
  public ImmutableList<GithubRepo> findAll() {
    return databaseClient
        .sql(
            "SELECT owner, repo, created_at, updated_at, action_owner, is_team_label_enabled"
                + " FROM github_repo")
        .map(this::toGithubRepo)
        .all()
        .collect(toImmutableList())
        .block();
  }

  private GithubRepo toGithubRepo(Readable row) {
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
