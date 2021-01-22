package build.bazel.dashboard.github.task;

import build.bazel.dashboard.github.GithubEventHandler;
import build.bazel.dashboard.github.api.GithubApi;
import build.bazel.dashboard.github.api.GithubApiResponse;
import build.bazel.dashboard.github.api.ListRepositoryEventsRequest;
import build.bazel.dashboard.utils.JsonStateStore;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Observable;
import io.reactivex.rxjava3.core.Single;
import lombok.Builder;
import lombok.RequiredArgsConstructor;
import lombok.Value;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.AbstractMap;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;

import static com.google.common.base.Preconditions.checkState;

@Component
@Slf4j
@RequiredArgsConstructor
public class PollGithubEventsTask {
  private final GithubApi githubApi;
  private final JsonStateStore jsonStateStore;
  private final GithubEventHandler githubEventHandler;

  @Builder
  @Value
  static class PollState {
    String etag;
    long eventId;
  }

  @Scheduled(fixedRate = 60000)
  public void pollGithubRepositoryEvents() {
    // TODO(coeuvre): Also poll other repos?
    pollGithubRepositoryEvents("bazelbuild", "bazel").blockingAwait();
  }

  public Completable pollGithubRepositoryEvents(String owner, String repo) {
    String stateKey = buildPollGithubRepositoryEventsStateKey(owner, repo);
    return jsonStateStore
        .load(stateKey, PollState.class)
        .flatMapCompletable(
            jsonState -> {
              int perPage = 30;
              AtomicReference<PollState> newStateRef = new AtomicReference<>(null);
              PollState state =
                  Optional.ofNullable(jsonState.getData())
                      .orElse(PollState.builder().etag("").eventId(0L).build());

              Observable<Single<Map.Entry<ListRepositoryEventsRequest, GithubApiResponse>>>
                  requests =
                  Observable.range(1, 10)
                      .map(
                          page ->
                              Single.defer(
                                  () -> {
                                    ListRepositoryEventsRequest
                                        .ListRepositoryEventsRequestBuilder
                                        builder =
                                        ListRepositoryEventsRequest.builder()
                                            .owner(owner)
                                            .repo(repo)
                                            .perPage(perPage)
                                            .page(page);
                                    if (page == 1) {
                                      builder.etag(state.getEtag());
                                    }
                                    ListRepositoryEventsRequest request = builder.build();
                                    return githubApi
                                        .listRepositoryEvents(request)
                                        .map(
                                            response ->
                                                new AbstractMap.SimpleEntry<>(
                                                    request, response));
                                  }));

              return Single.concat(requests)
                  .takeUntil(
                      entry -> {
                        GithubApiResponse response = entry.getValue();

                        boolean terminate = false;

                        if (response.getStatus().is2xxSuccessful()) {
                          JsonNode body = response.getBody();
                          checkState(body != null && body.isArray());

                          for (JsonNode event : body) {
                            if (event.get("id").asLong() <= state.getEventId()) {
                              terminate = true;
                              break;
                            }
                          }
                        } else {
                          terminate = true;
                        }

                        log.debug("{}", response);

                        return terminate;
                      })
                  .flatMapCompletable(
                      entry -> {
                        ListRepositoryEventsRequest request = entry.getKey();
                        GithubApiResponse response = entry.getValue();
                        JsonNode body = response.getBody();

                        if (body != null) {
                          if (request.getPage() == 1) {
                            newStateRef.set(
                                PollState.builder()
                                    .etag(response.getEtag())
                                    .eventId(body.get(0).get("id").asLong())
                                    .build());
                          }

                          return Observable.fromIterable(body)
                              .cast(ObjectNode.class)
                              .filter(event -> event.get("id").asLong() > state.getEventId())
                              .flatMapCompletable(
                                  event ->
                                      githubEventHandler.onGithubRepositoryEvent(
                                          owner, repo, event));
                        } else {
                          return Completable.complete();
                        }
                      })
                  .andThen(
                      Completable.defer(
                          () -> {
                            PollState newState = newStateRef.getAndSet(null);
                            if (newState != null) {
                              return jsonStateStore.save(
                                  jsonState.getKey(), jsonState.getTimestamp(), newState);
                            } else {
                              return Completable.complete();
                            }
                          }));
            });
  }

  private String buildPollGithubRepositoryEventsStateKey(String owner, String repo) {
    return String.format("poll-github-repository-events/%s/%s", owner, repo);
  }
}
