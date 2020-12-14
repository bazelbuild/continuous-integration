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
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.util.UriComponentsBuilder;
import reactor.adapter.rxjava.RxJava3Adapter;
import reactor.core.publisher.Mono;

import java.io.IOException;
import java.net.URLEncoder;
import java.time.Duration;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import static java.nio.charset.StandardCharsets.UTF_8;

/** Fetch github team issues by directly requesting the web pages and parse the HTML content. */
@Component
@Slf4j
@RequiredArgsConstructor
public class GithubTeamIssueCrawler implements GithubTeamIssueProvider {
  private static final String OWNER = "bazelbuild";
  private static final String REPO = "bazel";

  private final WebClient webClient;
  private final AsyncLoadingCache<GithubTeamIssue.Team, GithubTeamIssue> cache =
      Caffeine.newBuilder()
          .refreshAfterWrite(Duration.ofMinutes(1))
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

  @Override
  public Observable<GithubTeamIssue> list() {
    List<GithubTeamIssue.Team> teams =
        Arrays.asList(
            GithubTeamIssue.Team.builder()
                .label("team-Android")
                .name("Android")
                .owner("ahumesky")
                .build(),
            GithubTeamIssue.Team.builder().label("team-Apple").name("Apple").owner("aiuto").build(),
            GithubTeamIssue.Team.builder()
                .label("team-Bazel")
                .name("Bazel")
                .owner("stiffe")
                .build(),
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
      queryMap.put(
          KEY_ALL, String.format("is:issue is:open sort:updated-desc label:%s", teamLabel));
      queryMap.put(KEY_P0, String.format("is:issue is:open label:p0 label:%s", teamLabel));
      queryMap.put(KEY_P1, String.format("is:issue is:open label:p1 label:%s", teamLabel));
      queryMap.put(KEY_P2, String.format("is:issue is:open label:p2 label:%s", teamLabel));
      queryMap.put(KEY_P3, String.format("is:issue is:open label:p3 label:%s", teamLabel));
      queryMap.put(KEY_P4, String.format("is:issue is:open label:p4 label:%s", teamLabel));
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
                  + "label:%s",
              teamLabel));
      queryMap.put(
          KEY_NO_PRIORITY,
          String.format(
              "is:issue is:open "
                  + "-label:p0 "
                  + "-label:p1 "
                  + "-label:p2 "
                  + "-label:p3 "
                  + "-label:p4 "
                  + "label:%s",
              teamLabel));
      queryMap.put(
          KEY_UNTRIAGED, String.format("is:issue is:open label:untriaged label:%s", teamLabel));
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
        .queryParam("q", query)
        .build()
        .toString();
  }

  private static final Pattern OPEN_ISSUES_PATTERN = Pattern.compile("([0-9]+) Open");

  private Single<GithubTeamIssue.Stats> fetchIssuesStats(String query) {
    String url = buildQueryUrl(query);
    Mono<String> fetch =
        webClient
            .get()
            .uri(url)
            .exchangeToMono(
                clientResponse -> {
                  if (clientResponse.statusCode().is2xxSuccessful()) {
                    return clientResponse.bodyToMono(String.class);
                  }
                  return Mono.error(new IOException(clientResponse.statusCode().toString()));
                });
    return RxJava3Adapter.monoToSingle(fetch)
        .map(
            content -> {
              GithubTeamIssue.Stats.StatsBuilder builder = GithubTeamIssue.Stats.builder();
              builder.url(buildQueryUrl(URLEncoder.encode(query, UTF_8)));

              Matcher matcher = OPEN_ISSUES_PATTERN.matcher(content);
              if (matcher.find()) {
                String numberText = matcher.group(1);
                builder.count(Integer.parseInt(numberText));
              }

              return builder.build();
            });
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
