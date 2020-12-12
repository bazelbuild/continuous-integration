package build.bazel.dashboard.github.issue.rest;

import build.bazel.dashboard.github.api.GithubApi;
import build.bazel.dashboard.github.api.GetIssueRequest;
import build.bazel.dashboard.github.issue.*;
import lombok.Builder;
import lombok.RequiredArgsConstructor;
import lombok.Value;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Instant;
import java.util.concurrent.atomic.AtomicBoolean;

import static com.google.common.base.Preconditions.checkNotNull;

@RestController
@RequiredArgsConstructor
@Slf4j
public class GithubTeamIssuesRestController {
  private final GithubTeamIssueProvider githubTeamIssueProvider;
  private final GithubApi githubApi;
  private final GithubIssueRepository githubIssueRepository;

  @GetMapping("/github/teams/issues")
  public Flux<GithubTeamIssue> listGithubTeamIssues() {
    return githubTeamIssueProvider.list();
  }

  @GetMapping("/github/issues")
  public Flux<GithubIssueRepository.GithubIssue> listGithubIssues() {
    return githubIssueRepository.list();
  }

  @GetMapping("/github/{owner}/{repo}/issues/{issueNumber}")
  public Mono<GithubIssueRepository.GithubIssue> findOneGithubIssue(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @PathVariable("issueNumber") Integer issueNumber) {
    return githubIssueRepository.findOne(owner, repo, issueNumber);
  }

  @PutMapping("/github/{owner}/{repo}/issues/{issueNumber}")
  public Mono<GithubIssueRepository.GithubIssue> updateGithubIssue(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @PathVariable("issueNumber") Integer issueNumber) {
    return fetchOneIssues(owner, repo, issueNumber).map(it -> it.result);
  }

  @Builder
  @Value
  static class UpdateResult {
    int count;
    int added;
    int updated;
    int untouched;
    int error;
  }

  @Builder
  @Value
  static class UpdateResultOne {
    GithubIssueRepository.GithubIssue result;
    boolean added;
    boolean updated;
    boolean error;

    static UpdateResultOne create(
        GithubIssueRepository.GithubIssue result, boolean exists, boolean saved, boolean error) {
      UpdateResultOneBuilder builder = UpdateResultOne.builder().result(result);
      if (error) {
        builder.error(true);
      } else if (saved) {
        if (exists) {
          builder.updated(true);
        } else {
          builder.added(true);
        }
      }
      return builder.build();
    }
  }

  private Mono<UpdateResultOne> fetchOneIssues(String owner, String repo, Integer issueNumber) {
    AtomicBoolean exists = new AtomicBoolean(false);
    return githubIssueRepository
        .findOne(owner, repo, issueNumber)
        .doOnNext((it) -> exists.set(true))
        .switchIfEmpty(Mono.just(GithubIssueRepository.GithubIssue.empty(owner, repo, issueNumber)))
        .flatMap(
            existingGithubIssue -> {
              GetIssueRequest request =
                  GetIssueRequest.builder()
                      .owner(owner)
                      .repo(repo)
                      .issueNumber(issueNumber)
                      .eTag(existingGithubIssue.getETag())
                      .build();

              return githubApi
                  .getIssue(request)
                  .flatMap(
                      response -> {
                        if (response.getStatus().is2xxSuccessful()) {
                          GithubIssueRepository.GithubIssue githubIssue =
                              GithubIssueRepository.GithubIssue.builder()
                                  .owner(owner)
                                  .repo(repo)
                                  .issueNumber(issueNumber)
                                  .timestamp(Instant.now())
                                  .eTag(response.getETag())
                                  .data(response.getBody())
                                  .build();
                          return githubIssueRepository
                              .save(githubIssue)
                              .map(it -> UpdateResultOne.create(it, exists.get(), true, false));
                        } else if (response.getStatus().value() == 304) {
                          // Not modified
                          return Mono.just(
                              UpdateResultOne.create(existingGithubIssue, true, false, false));
                        } else {
                          log.error(
                              "Failed to fetch {}/{}/issues/{}: {}",
                              owner,
                              repo,
                              issueNumber,
                              response.getStatus().toString());
                          return Mono.just(
                              UpdateResultOne.create(
                                  existingGithubIssue, exists.get(), false, true));
                        }
                      });
            });
  }

  @PutMapping("/github/{owner}/{repo}/issues")
  public Mono<UpdateResult> updateGithubIssues(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @RequestParam(name = "start") Integer start,
      @RequestParam(name = "count") Integer count) {
    checkNotNull(start);
    checkNotNull(count);
    return Flux.range(start, count)
        .flatMapSequential(
            issueNumber -> fetchOneIssues(owner, repo, issueNumber),
            10) // Limit concurrent request to 10 so we won't rate limited by Github
        .collect(
            UpdateResult::builder,
            (builder, result) -> {
              if (result.isAdded()) {
                builder.added(builder.added + 1);
              } else if (result.isUpdated()) {
                builder.updated(builder.updated + 1);
              } else if (result.isError()) {
                builder.error(builder.error + 1);
              } else {
                builder.untouched(builder.untouched + 1);
              }
            })
        .map(builder -> builder.count(count).build());
  }
}
