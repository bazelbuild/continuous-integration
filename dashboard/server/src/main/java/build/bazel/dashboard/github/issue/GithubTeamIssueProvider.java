package build.bazel.dashboard.github.issue;

import build.bazel.dashboard.utils.RxJavaFutures;
import com.github.benmanes.caffeine.cache.AsyncCacheLoader;
import com.github.benmanes.caffeine.cache.AsyncLoadingCache;
import com.github.benmanes.caffeine.cache.Caffeine;
import io.reactivex.rxjava3.core.Observable;
import io.reactivex.rxjava3.core.Single;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.checkerframework.checker.nullness.qual.NonNull;
import org.springframework.stereotype.Component;
import org.springframework.web.util.UriComponentsBuilder;

import java.net.URLEncoder;
import java.time.Duration;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.stream.Collectors;

import static java.nio.charset.StandardCharsets.UTF_8;

/**
 * Fetch github team issues by directly requesting the web pages and parse the HTML content.
 */
@Component
@Slf4j
@RequiredArgsConstructor
public class GithubTeamIssueProvider {
  private static final String OWNER = "bazelbuild";
  private static final String REPO = "bazel";

  private final GithubSearchExecutor githubSearchExecutor;
  private final AsyncLoadingCache<GithubTeamIssue.Team, GithubTeamIssue> cache =
      Caffeine.newBuilder()
          .refreshAfterWrite(Duration.ofSeconds(1))
          .buildAsync(
              new AsyncCacheLoader<>() {
                @Override
                public @NonNull CompletableFuture<GithubTeamIssue> asyncLoad(
                    GithubTeamIssue.@NonNull Team key, @NonNull Executor executor) {
                  Single<GithubTeamIssue> single =
                      fetchTeamIssue(key)
                          .doOnError(error -> log.error("Failed to fetch issues", error))
                          // If we encounter some errors when the first time fetching the data,
                          // return a
                          // ZERO data to make sure we can continue.
                          .onErrorResumeNext(error -> Single.just(buildEmptyTeamIssue(key)));
                  return RxJavaFutures.toCompletableFuture(single, executor);
                }

                @Override
                public @NonNull CompletableFuture<GithubTeamIssue> asyncReload(
                    GithubTeamIssue.@NonNull Team key,
                    @NonNull GithubTeamIssue oldValue,
                    @NonNull Executor executor) {
                  // Only reload after 10 minutes to avoid Github rate limit
                  if (oldValue
                      .getUpdatedAt()
                      .plus(10, ChronoUnit.MINUTES)
                      .isBefore(Instant.now())) {
                    Single<GithubTeamIssue> single =
                        fetchTeamIssue(key)
                            .doOnError(error -> log.error("Failed to fetch issues", error));
                    return RxJavaFutures.toCompletableFuture(single, executor);
                  } else {
                    return CompletableFuture.completedFuture(oldValue);
                  }
                }
              });

  private static final List<GithubTeamIssue.Team> teams =
      Arrays.asList(
          GithubTeamIssue.Team.builder().label("none").name("(none)").owner("").build(),
          GithubTeamIssue.Team.builder()
              .label("team-Android")
              .name("Android")
              .owner("ahumesky")
              .build(),
          GithubTeamIssue.Team.builder().label("team-Apple").name("Apple").owner("aiuto").build(),
          GithubTeamIssue.Team.builder().label("team-Bazel").name("Bazel").owner("stiffe").build(),
          GithubTeamIssue.Team.builder()
              .label("team-Configurability")
              .name("Configurability")
              .owner("gregestren")
              .build(),
          GithubTeamIssue.Team.builder().label("team-Core").name("Core").owner("janakr").build(),
          GithubTeamIssue.Team.builder()
              .label("team-Documentation")
              .name("Documentation")
              .owner("daroberts")
              .build(),
          GithubTeamIssue.Team.builder()
              .label("team-Local-Exec")
              .name("Local-Exec")
              .owner("twerth")
              .build(),
          GithubTeamIssue.Team.builder()
              .label("team-Performance")
              .name("Performance")
              .owner("twerth")
              .build(),
          GithubTeamIssue.Team.builder()
              .label("team-Remote-Exec")
              .name("Remote-Exec")
              .owner("chiwang")
              .build(),
          GithubTeamIssue.Team.builder()
              .label("team-Rules-CPP")
              .name("Rules-CPP")
              .owner("lberki")
              .build(),
          GithubTeamIssue.Team.builder()
              .label("team-Rules-Java")
              .name("Rules-Java")
              .owner("lberki")
              .build(),
          GithubTeamIssue.Team.builder()
              .label("team-Rules-Python")
              .name("Rules-Python")
              .owner("lberki")
              .build(),
          GithubTeamIssue.Team.builder()
              .label("team-Rules-Server")
              .name("Rules-Server")
              .owner("lberki")
              .build(),
          GithubTeamIssue.Team.builder()
              .label("team-Starlark")
              .name("Starlark")
              .owner("adonovan")
              .build(),
          GithubTeamIssue.Team.builder()
              .label("team-XProduct")
              .name("XProduct")
              .owner("philwo")
              .build());

  public Observable<GithubTeamIssue> list() {
    return Observable.fromIterable(teams)
        // We could have use flatMap here to fetch all the team issues CONCURRENTLY. However it
        // will lead us an error of 429 TOO_MANY_REQUESTS since Github has rate limit...
        .flatMap(team -> Single.fromFuture(cache.get(team)).toObservable())
        .sorted(Comparator.comparing(a -> a.getTeam().getName()));
  }

  static class TeamIssueBuilder {
    static final String KEY_ALL = "all";
    static final String KEY_P0 = "p0";
    static final String KEY_P1 = "p1";
    static final String KEY_P2 = "p2";
    static final String KEY_P3 = "p3";
    static final String KEY_P4 = "p4";
    static final String KEY_NO_TYPE = "noType";
    static final String KEY_NO_PRIORITY = "noPriority";
    static final String KEY_UNTRIAGED = "untriaged";

    final Map<String, String> queryMap = new HashMap<>();
    final GithubTeamIssue.GithubTeamIssueBuilder builder = GithubTeamIssue.builder();

    TeamIssueBuilder(GithubTeamIssue.Team team) {
      builder.team(team);

      String teamLabel = team.getLabel();
      String teamQuery;
      if (teamLabel.equals("none")) {
        teamQuery =
            teams.stream()
                .map(GithubTeamIssue.Team::getLabel)
                .filter(label -> !label.equals("none"))
                .map(label -> "-label:" + label)
                .collect(Collectors.joining(" "));
      } else {
        teamQuery = "label:" + teamLabel;
      }
      queryMap.put(KEY_ALL, String.format("is:issue is:open %s", teamQuery));
      queryMap.put(KEY_P0, String.format("is:issue is:open label:P0 %s", teamQuery));
      queryMap.put(KEY_P1, String.format("is:issue is:open label:P1 %s", teamQuery));
      queryMap.put(KEY_P2, String.format("is:issue is:open label:P2 %s", teamQuery));
      queryMap.put(KEY_P3, String.format("is:issue is:open label:P3 %s", teamQuery));
      queryMap.put(KEY_P4, String.format("is:issue is:open label:P4 %s", teamQuery));
      // TODO(coeuvre): Fetch all labels so we don't need to hardcode this
      queryMap.put(
          KEY_NO_TYPE,
          String.format(
              "is:issue is:open "
                  + "-label:\"type: process\" "
                  + "-label:\"type: support / not a bug (process)\" "
                  + "-label:\"type: documentation (cleanup)\" "
                  + "-label:\"type: bug\" "
                  + "-label:\"type: feature request\" "
                  + "%s",
              teamQuery));
      queryMap.put(
          KEY_NO_PRIORITY,
          String.format(
              "is:issue is:open "
                  + "-label:P0 "
                  + "-label:P1 "
                  + "-label:P2 "
                  + "-label:P3 "
                  + "-label:P4 "
                  + "%s",
              teamQuery));
      queryMap.put(
          KEY_UNTRIAGED, String.format("is:issue is:open label:untriaged %s", teamQuery));
    }

    public void collectIssueStats(Map.Entry<String, GithubTeamIssue.Stats> entry) {
      String key = entry.getKey();
      GithubTeamIssue.Stats value = entry.getValue();
      switch (key) {
        case KEY_ALL:
          builder.openIssues(value);
          break;
        case KEY_P0:
          builder.openP0Issues(value);
          break;
        case KEY_P1:
          builder.openP1Issues(value);
          break;
        case KEY_P2:
          builder.openP2Issues(value);
          break;
        case KEY_P3:
          builder.openP3Issues(value);
          break;
        case KEY_P4:
          builder.openP4Issues(value);
          break;
        case KEY_NO_TYPE:
          builder.openNoTypeIssues(value);
          break;
        case KEY_NO_PRIORITY:
          builder.openNoPriorityIssues(value);
          break;
        case KEY_UNTRIAGED:
          builder.openUntriagedIssues(value);
          break;
      }
    }

    public Set<Map.Entry<String, String>> queryEntrySet() {
      return queryMap.entrySet();
    }

    public TeamIssueBuilder updatedAt(Instant updatedAt) {
      builder.updatedAt(updatedAt);
      return this;
    }

    public GithubTeamIssue build() {
      return builder.build();
    }
  }

  private Single<GithubTeamIssue> fetchTeamIssue(GithubTeamIssue.Team team) {
    TeamIssueBuilder builder = new TeamIssueBuilder(team);
    return Observable.fromIterable(builder.queryEntrySet())
        .flatMap(
            entry ->
                fetchIssuesStats(entry.getValue())
                    .map(number -> new AbstractMap.SimpleEntry<>(entry.getKey(), number))
                    .toObservable())
        .collect(() -> builder, TeamIssueBuilder::collectIssueStats)
        .map(b -> b.updatedAt(Instant.now()).build());
  }

  private static String buildQueryUrl(String query) {
    return UriComponentsBuilder.newInstance()
        .scheme("https")
        .host("github.com")
        .pathSegment(OWNER, REPO, "issues")
        .queryParam("q", URLEncoder.encode(query, UTF_8))
        .build()
        .toString();
  }

  private Single<GithubTeamIssue.Stats> fetchIssuesStats(String query) {
    return githubSearchExecutor
        .fetchSearchResultCount(OWNER, REPO, query)
        .onErrorComplete(
            error -> {
              log.error(String.format("Failed to fetch issues stats with query %s", query), error);
              return true;
            })
        .map(
            count -> GithubTeamIssue.Stats.builder().url(buildQueryUrl(query)).count(count).build())
        .defaultIfEmpty(GithubTeamIssue.Stats.builder().url(buildQueryUrl(query)).build());
  }

  private static GithubTeamIssue buildEmptyTeamIssue(GithubTeamIssue.Team team) {
    TeamIssueBuilder builder = new TeamIssueBuilder(team);
    builder.queryEntrySet().stream()
        .map(
            entry -> {
              String query = entry.getValue();
              String url = buildQueryUrl(URLEncoder.encode(query, UTF_8));
              GithubTeamIssue.Stats stats = GithubTeamIssue.Stats.builder().url(url).build();
              return new AbstractMap.SimpleEntry<>(entry.getKey(), stats);
            })
        .forEach(builder::collectIssueStats);
    builder.updatedAt(Instant.EPOCH);
    return builder.build();
  }
}
