package build.bazel.dashboard.github.sync.event;

import static build.bazel.dashboard.utils.RxJavaVirtualThread.completable;
import static com.google.common.base.Preconditions.checkState;

import build.bazel.dashboard.github.api.GithubApi;
import build.bazel.dashboard.github.api.GithubApiResponse;
import build.bazel.dashboard.github.api.ListRepositoryEventsRequest;
import build.bazel.dashboard.github.api.ListRepositoryIssueEventsRequest;
import build.bazel.dashboard.github.repo.GithubRepoService;
import build.bazel.dashboard.utils.JsonStateStore;
import build.bazel.dashboard.utils.JsonStateStore.JsonState;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.reactivex.rxjava3.core.Completable;
import java.util.Optional;
import lombok.Builder;
import lombok.RequiredArgsConstructor;
import lombok.Value;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RestController;

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

    public static PollState createEmpty() {
      return PollState.builder().etag("").eventId(0L).build();
    }

    public static PollState create(String etag, long eventId) {
      return PollState.builder().etag(etag).eventId(eventId).build();
    }
  }

  @Scheduled(fixedDelay = 1000)
  public void pollGithubEvents() {
    for (var githubRepo : githubRepoService.findAll()) {
      String owner = githubRepo.getOwner();
      String repo = githubRepo.getRepo();
      doPollGithubRepositoryEvents(owner, repo);
      doPollGithubRepositoryIssueEvents(owner, repo);
    }
  }

  @PutMapping("/internal/github/{owner}/{repo}/events")
  public Completable pollGithubRepositoryEvents(
      @PathVariable("owner") String owner, @PathVariable("repo") String repo) {
    return completable(() -> doPollGithubRepositoryEvents(owner, repo));
  }

  private void doPollGithubRepositoryEvents(String owner, String repo) {
    String stateKey = buildPollGithubRepositoryEventsStateKey(owner, repo);
    var poller =
        new PagePoller(owner, repo, stateKey) {
          @Override
          public GithubApiResponse doRequest(
              String owner, String repo, int perPage, int page, String etag) {
            var request =
                ListRepositoryEventsRequest.builder()
                    .owner(owner)
                    .repo(repo)
                    .perPage(perPage)
                    .etag(etag)
                    .page(page)
                    .build();
            return githubApi.listRepositoryEvents(request);
          }

          @Override
          public void onEvent(String owner, String repo, ObjectNode event) {
            githubEventHandler.onGithubRepositoryEvent(owner, repo, event);
          }
        };
    poller.poll();
  }

  @PutMapping("/internal/github/{owner}/{repo}/issues/events")
  public Completable pollGithubRepositoryIssueEvents(
      @PathVariable("owner") String owner, @PathVariable("repo") String repo) {
    return completable(() -> doPollGithubRepositoryIssueEvents(owner, repo));
  }

  private void doPollGithubRepositoryIssueEvents(String owner, String repo) {
    String stateKey = buildPollGithubRepositoryIssueEventsStateKey(owner, repo);
    var poller =
        new PagePoller(owner, repo, stateKey) {
          @Override
          public GithubApiResponse doRequest(
              String owner, String repo, int perPage, int page, String etag) {
            var request =
                ListRepositoryIssueEventsRequest.builder()
                    .owner(owner)
                    .repo(repo)
                    .perPage(perPage)
                    .etag(etag)
                    .page(page)
                    .build();
            return githubApi.listRepositoryIssueEvents(request);
          }

          @Override
          public void onEvent(String owner, String repo, ObjectNode event) {
            githubEventHandler.onGithubRepositoryIssueEvent(owner, repo, event);
          }
        };
    poller.poll();
  }

  abstract class PagePoller {
    private final String owner;
    private final String repo;
    private final String stateKey;

    public PagePoller(String owner, String repo, String stateKey) {
      this.owner = owner;
      this.repo = repo;
      this.stateKey = stateKey;
    }

    public abstract GithubApiResponse doRequest(
        String owner, String repo, int perPage, int page, String etag);

    public abstract void onEvent(String owner, String repo, ObjectNode event);

    public void poll() {
      var jsonState = jsonStateStore.load(stateKey, PollState.class);
      var state = Optional.ofNullable(jsonState.getData()).orElse(PollState.createEmpty());

      JsonState<PollState> newState = null;
      int perPage = 30;
      for (var page = 1; page < 10; page++) {
        var etag = "";
        if (page == 1 && state.getEtag() != null) {
          etag = state.getEtag();
        }
        var response = doRequest(owner, repo, perPage, page, etag);

        if (shouldTerminate(state, response)) {
          break;
        }

        var body = response.getBody();
        if (page == 1) {
          newState =
              JsonState.<PollState>builder()
                  .key(jsonState.getKey())
                  .timestamp(jsonState.getTimestamp())
                  .data(PollState.create(response.getEtag(), body.get(0).get("id").asLong()))
                  .build();
        }

        for (var item : body) {
          var event = (ObjectNode) item;
          if (event.get("id").asLong() <= state.getEventId()) {
            continue;
          }
          onEvent(owner, repo, event);
        }
      }

      if (newState != null) {
        jsonStateStore.save(newState.getKey(), newState.getTimestamp(), newState.getData());
      }
    }

    private static boolean shouldTerminate(PollState state, GithubApiResponse response) {
      boolean terminate = false;

      if (response.getStatus().is2xxSuccessful()) {
        JsonNode body = response.getBody();
        checkState(body != null && body.isArray());

        var hasNewEvent = false;
        for (JsonNode event : body) {
          if (event.get("id").asLong() > state.getEventId()) {
            hasNewEvent = true;
            break;
          }
        }

        if (!hasNewEvent) {
          terminate = true;
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
  }

  private String buildPollGithubRepositoryEventsStateKey(String owner, String repo) {
    return String.format("poll-github-repository-events/%s/%s", owner, repo);
  }

  private String buildPollGithubRepositoryIssueEventsStateKey(String owner, String repo) {
    return String.format("poll-github-repository-issue-events/%s/%s", owner, repo);
  }
}
