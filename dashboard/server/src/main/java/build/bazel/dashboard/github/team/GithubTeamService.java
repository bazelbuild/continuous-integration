package build.bazel.dashboard.github.team;

import build.bazel.dashboard.utils.RxJavaFutures;
import com.github.benmanes.caffeine.cache.AsyncCacheLoader;
import com.github.benmanes.caffeine.cache.AsyncLoadingCache;
import com.github.benmanes.caffeine.cache.Caffeine;
import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Single;
import lombok.Builder;
import lombok.RequiredArgsConstructor;
import lombok.Value;
import lombok.extern.slf4j.Slf4j;
import org.checkerframework.checker.nullness.qual.NonNull;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.stream.Collectors;

@Service
@Slf4j
@RequiredArgsConstructor
public class GithubTeamService {
  private final GithubTeamRepo githubTeamRepo;

  @Builder
  @Value
  static class TeamsCacheKey {
    String owner;
    String repo;
  }

  private final AsyncLoadingCache<TeamsCacheKey, List<GithubTeam>> teamsCache =
      Caffeine.newBuilder()
          .refreshAfterWrite(Duration.ofMinutes(1))
          .buildAsync(
              new AsyncCacheLoader<>() {
                @Override
                public @NonNull CompletableFuture<List<GithubTeam>> asyncLoad(
                    @NonNull TeamsCacheKey key, @NonNull Executor executor) {
                  Single<List<GithubTeam>> single =
                      githubTeamRepo
                          .list(key.getOwner(), key.getRepo())
                          .collect(Collectors.toList());
                  return RxJavaFutures.toCompletableFuture(single, executor);
                }
              });

  private static TeamsCacheKey buildTeamsKey(String owner, String repo) {
    return TeamsCacheKey.builder().owner(owner).repo(repo).build();
  }

  public Flowable<GithubTeam> findAll(String owner, String repo) {
    return Single.fromFuture(teamsCache.get(buildTeamsKey(owner, repo)))
        .flatMapPublisher(Flowable::fromIterable);
  }
}
