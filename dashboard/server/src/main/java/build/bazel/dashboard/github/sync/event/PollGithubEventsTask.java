package build.bazel.dashboard.github.sync.event;

import build.bazel.dashboard.github.api.GithubApi;
import build.bazel.dashboard.github.api.GithubApiResponse;
import build.bazel.dashboard.github.api.ListRepositoryEventsRequest;
import build.bazel.dashboard.github.api.ListRepositoryEventsRequest.ListRepositoryEventsRequestBuilder;
import build.bazel.dashboard.github.api.ListRepositoryIssueEventsRequest;
import build.bazel.dashboard.github.api.ListRepositoryIssueEventsRequest.ListRepositoryIssueEventsRequestBuilder;
import build.bazel.dashboard.github.repo.GithubRepoService;
import build.bazel.dashboard.utils.JsonStateStore;
import build.bazel.dashboard.utils.JsonStateStore.JsonState;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Maybe;
import lombok.Builder;
import lombok.RequiredArgsConstructor;
import lombok.Value;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;

import static com.google.common.base.Preconditions.checkState;

@RestController
@Slf4j
@RequiredArgsConstructor
public class PollGithubEventsTask {
  private final GithubApi githubApi;
  private final JsonStateStore jsonStateStore;
  private final GithubEventHandler githubEventHandler;
  private final GithubRepoService githubRepoService;

  @Builder
  @Value
  static class PollState {
    String etag;
    long eventId;
  }

//  @Scheduled(fixedDelay = 60000)
  public void pollGithubEvents() {
    githubRepoService
        .findAll()
        .flatMapCompletable(
            githubRepo -> {
              String owner = githubRepo.getOwner();
              String repo = githubRepo.getRepo();
              return pollGithubRepositoryEvents(owner, repo)
                  .andThen(pollGithubRepositoryIssueEvents(owner, repo));
            },
            false,
            1)
        .blockingAwait();
  }

  @PutMapping("/github/{owner}/{repo}/events")
  public Completable pollGithubRepositoryEvents(
      @PathVariable("owner") String owner, @PathVariable("repo") String repo) {
    String stateKey = buildPollGithubRepositoryEventsStateKey(owner, repo);
    return jsonStateStore
        .load(stateKey, PollState.class)
        .flatMapMaybe(
            jsonState -> {
              PollState state =
                  Optional.ofNullable(jsonState.getData())
                      .orElse(PollState.builder().etag("").eventId(0L).build());
              AtomicReference<JsonState<PollState>> newStateRef = new AtomicReference<>(null);

              return listRepositoryEvents(owner, repo, state.getEtag())
                  .takeUntil(
                      result -> {
                        return shouldTerminate(state, result.getResponse());
                      })
                  .filter(result -> result.getResponse().getBody() != null)
                  .doOnNext(
                      result -> {
                        ListRepositoryEventsRequest request = result.getRequest();
                        if (request.getPage() == 1) {
                          updateNewStateRef(jsonState, newStateRef, result.getResponse());
                        }
                      })
                  .flatMapCompletable(
                      result -> {
                        GithubApiResponse response = result.getResponse();
                        JsonNode body = response.getBody();

                        return Flowable.fromIterable(body)
                            .cast(ObjectNode.class)
                            .filter(event -> event.get("id").asLong() > state.getEventId())
                            .flatMapCompletable(
                                event ->
                                    githubEventHandler.onGithubRepositoryEvent(owner, repo, event),
                                false,
                                1);
                      },
                      false,
                      1)
                  .andThen(Maybe.fromCallable(newStateRef::get));
            })
        .flatMapCompletable(
            jsonState ->
                jsonStateStore.save(
                    jsonState.getKey(), jsonState.getTimestamp(), jsonState.getData()));
  }

  @PutMapping("/github/{owner}/{repo}/issues/events")
  public Completable pollGithubRepositoryIssueEvents(
      @PathVariable("owner") String owner, @PathVariable("repo") String repo) {
    String stateKey = buildPollGithubRepositoryIssueEventsStateKey(owner, repo);
    return jsonStateStore
        .load(stateKey, PollState.class)
        .flatMapMaybe(
            jsonState -> {
              PollState state =
                  Optional.ofNullable(jsonState.getData())
                      .orElse(PollState.builder().etag("").eventId(0L).build());
              AtomicReference<JsonState<PollState>> newStateRef = new AtomicReference<>(null);
              return listRepositoryIssueEvents(owner, repo, state.getEtag())
                  .takeUntil(
                      result -> {
                        return shouldTerminate(state, result.getResponse());
                      })
                  .filter(result -> result.getResponse().getBody() != null)
                  .doOnNext(
                      result -> {
                        ListRepositoryIssueEventsRequest request = result.getRequest();
                        if (request.getPage() == 1) {
                          updateNewStateRef(jsonState, newStateRef, result.getResponse());
                        }
                      })
                  .flatMapCompletable(
                      result -> {
                        GithubApiResponse response = result.getResponse();
                        JsonNode body = response.getBody();

                        return Flowable.fromIterable(body)
                            .cast(ObjectNode.class)
                            .filter(event -> event.get("id").asLong() > state.getEventId())
                            .flatMapCompletable(
                                event ->
                                    githubEventHandler.onGithubRepositoryIssueEvent(
                                        owner, repo, event),
                                false,
                                1);
                      },
                      false,
                      1)
                  .andThen(Maybe.fromCallable(newStateRef::get));
            })
        .flatMapCompletable(
            jsonState ->
                jsonStateStore.save(
                    jsonState.getKey(), jsonState.getTimestamp(), jsonState.getData()));
  }

  private boolean shouldTerminate(PollState state, GithubApiResponse response) {
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

    log.debug(
        "status={}, etag={}, rateLimit={}",
        response.getStatus(),
        response.getEtag(),
        response.getRateLimit());

    return terminate;
  }

  private void updateNewStateRef(
      JsonState<PollState> jsonState,
      AtomicReference<JsonState<PollState>> newStateRef,
      GithubApiResponse response) {
    JsonNode body = response.getBody();
    newStateRef.set(
        JsonState.<PollState>builder()
            .key(jsonState.getKey())
            .timestamp(jsonState.getTimestamp())
            .data(
                PollState.builder()
                    .etag(response.getEtag())
                    .eventId(body.get(0).get("id").asLong())
                    .build())
            .build());
  }

  @Builder
  @Value
  static class GithubApiResult<Req> {
    Req request;
    GithubApiResponse response;
  }

  private Flowable<GithubApiResult<ListRepositoryEventsRequest>> listRepositoryEvents(
      String owner, String repo, String etag) {
    int perPage = 30;

    return Flowable.range(1, 10)
        .map(
            page -> {
              ListRepositoryEventsRequestBuilder builder =
                  ListRepositoryEventsRequest.builder()
                      .owner(owner)
                      .repo(repo)
                      .perPage(perPage)
                      .page(page);
              if (page == 1 && etag != null) {
                builder.etag(etag);
              }
              return builder.build();
            })
        .flatMapSingle(
            request ->
                githubApi
                    .listRepositoryEvents(request)
                    .map(
                        response ->
                            GithubApiResult.<ListRepositoryEventsRequest>builder()
                                .request(request)
                                .response(response)
                                .build()),
            false,
            1);
  }

  private Flowable<GithubApiResult<ListRepositoryIssueEventsRequest>> listRepositoryIssueEvents(
      String owner, String repo, String etag) {
    int perPage = 30;

    return Flowable.range(1, 10)
        .map(
            page -> {
              ListRepositoryIssueEventsRequestBuilder builder =
                  ListRepositoryIssueEventsRequest.builder()
                      .owner(owner)
                      .repo(repo)
                      .perPage(perPage)
                      .page(page);
              if (page == 1 && etag != null) {
                builder.etag(etag);
              }
              return builder.build();
            })
        .flatMapSingle(
            request ->
                githubApi
                    .listRepositoryIssueEvents(request)
                    .map(
                        response ->
                            GithubApiResult.<ListRepositoryIssueEventsRequest>builder()
                                .request(request)
                                .response(response)
                                .build()),
            false,
            1);
  }

  private String buildPollGithubRepositoryEventsStateKey(String owner, String repo) {
    return String.format("poll-github-repository-events/%s/%s", owner, repo);
  }

  private String buildPollGithubRepositoryIssueEventsStateKey(String owner, String repo) {
    return String.format("poll-github-repository-issue-events/%s/%s", owner, repo);
  }
}
