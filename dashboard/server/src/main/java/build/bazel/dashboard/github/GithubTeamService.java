package build.bazel.dashboard.github;

import build.bazel.dashboard.github.db.GithubIssueTeamRepository;
import build.bazel.dashboard.utils.RxJavaFutures;
import com.github.benmanes.caffeine.cache.AsyncCache;
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
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.stream.Collectors;

/**
 * Fetch github team issues by directly requesting the web pages and parse the HTML content.
 */
@Component
@Slf4j
@RequiredArgsConstructor
public class GithubTeamService {
  private final GithubIssueTeamRepository githubIssueTeamRepository;
  private final GithubSearchService githubSearchService;

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
                      Flowable.concat(
                          Flowable.just(
                              GithubTeam.buildNone(key.getOwner(), key.getRepo())),
                          githubIssueTeamRepository.list(key.getOwner(), key.getRepo()))
                          .collect(Collectors.toList());
                  return RxJavaFutures.toCompletableFuture(single, executor);
                }
              });

  private final AsyncCache<GithubTeam, GithubTeamIssue> issueCache =
      Caffeine.newBuilder().expireAfterWrite(Duration.ofSeconds(1)).buildAsync();

  private static TeamsCacheKey buildTeamsKey(String owner, String repo) {
    return TeamsCacheKey.builder().owner(owner).repo(repo).build();
  }

  private CompletableFuture<GithubTeamIssue> loadIssue(
      String owner,
      String repo,
      List<GithubTeam> teams,
      GithubTeam key,
      Executor executor) {
    return RxJavaFutures.toCompletableFuture(fetchTeamIssue(owner, repo, teams, key), executor);
  }

  public Flowable<GithubTeamIssue> listIssues(String owner, String repo) {
    return Single.fromFuture(teamsCache.get(buildTeamsKey(owner, repo)))
        .flatMapPublisher(
            teams ->
                Flowable.fromIterable(teams)
                    .flatMap(
                        team ->
                            Flowable.fromFuture(
                                issueCache.get(
                                    team,
                                    (key, executor) ->
                                        loadIssue(owner, repo, teams, key, executor)))))
        .sorted(Comparator.comparing(issue -> issue.getTeam().getTeamOwner()));
  }

  private static String buildTeamQuery(List<GithubTeam> teams, GithubTeam team) {
    String teamLabel = team.getLabel();
    String teamQuery;
    if (teamLabel.equals("")) {
      teamQuery =
          teams.stream()
              .map(GithubTeam::getLabel)
              .filter(label -> !label.equals(""))
              .map(label -> "-label:" + label)
              .collect(Collectors.joining(" "));
    } else {
      teamQuery = "label:" + teamLabel;
    }

    return teamQuery;
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
    static final String KEY_PR = "pullRequest";

    final Map<String, String> queryMap = new HashMap<>();
    final GithubTeamIssue.GithubTeamIssueBuilder builder = GithubTeamIssue.builder();

    TeamIssueBuilder(List<GithubTeam> teams, GithubTeam team) {
      builder.team(team);

      String teamQuery = buildTeamQuery(teams, team);
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
      queryMap.put(KEY_UNTRIAGED, String.format("is:issue is:open label:untriaged %s", teamQuery));
      queryMap.put(KEY_PR, String.format("is:pr is:open %s", teamQuery));
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
        case KEY_PR:
          builder.openPullRequests(value);
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

  private Single<GithubTeamIssue> fetchTeamIssue(
      String owner, String repo, List<GithubTeam> teams, GithubTeam team) {
    TeamIssueBuilder builder = new TeamIssueBuilder(teams, team);
    return Flowable.fromIterable(builder.queryEntrySet())
        .flatMapSingle(
            entry ->
                fetchIssuesStats(owner, repo, entry.getValue())
                    .map(number -> new AbstractMap.SimpleEntry<>(entry.getKey(), number)))
        .collect(() -> builder, TeamIssueBuilder::collectIssueStats)
        .map(b -> b.updatedAt(Instant.now()).build());
  }

  private Single<GithubTeamIssue.Stats> fetchIssuesStats(String owner, String repo, String query) {
    return githubSearchService
        .fetchSearchResultCount(owner, repo, query)
        .onErrorComplete(
            error -> {
              log.error(String.format("Failed to fetch issues stats with query %s", query), error);
              return true;
            })
        .map(
            count ->
                GithubTeamIssue.Stats.builder()
                    .url(GithubUtils.buildIssueQueryUrl(owner, repo, query))
                    .count(count)
                    .build())
        .defaultIfEmpty(
            GithubTeamIssue.Stats.builder()
                .url(GithubUtils.buildIssueQueryUrl(owner, repo, query))
                .build());
  }
}
