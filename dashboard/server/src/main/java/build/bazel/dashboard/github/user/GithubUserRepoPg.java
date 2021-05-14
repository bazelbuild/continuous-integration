package build.bazel.dashboard.github.user;

import io.reactivex.rxjava3.core.Flowable;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;
import reactor.adapter.rxjava.RxJava3Adapter;
import reactor.core.publisher.Flux;

import static java.util.Objects.requireNonNull;

@Repository
@RequiredArgsConstructor
public class GithubUserRepoPg implements GithubUserRepo {
  private final DatabaseClient databaseClient;

  @Override
  public Flowable<GithubUser> findAll() {
    Flux<GithubUser> query =
        databaseClient
            .sql("SELECT username, email FROM github_user")
            .map(
                row ->
                    GithubUser.builder()
                        .username(requireNonNull(row.get("username", String.class)))
                        .email(requireNonNull(row.get("email", String.class)))
                        .build())
            .all();

    return RxJava3Adapter.fluxToFlowable(query);
  }
}
