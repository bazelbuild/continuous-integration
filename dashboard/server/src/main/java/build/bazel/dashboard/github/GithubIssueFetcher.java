package build.bazel.dashboard.github;

import build.bazel.dashboard.github.api.FetchIssueRequest;
import build.bazel.dashboard.github.api.GithubApi;
import build.bazel.dashboard.github.db.GithubIssueRepository;
import io.reactivex.rxjava3.core.Single;
import lombok.Builder;
import lombok.RequiredArgsConstructor;
import lombok.Value;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.time.Instant;

@Component
@Slf4j
@RequiredArgsConstructor
public class GithubIssueFetcher {

  private final GithubApi githubApi;
  private final GithubIssueRepository repository;

  @Builder
  @Value
  public static class FetchResult {
    GithubIssue githubIssue;
    boolean added;
    boolean updated;
    boolean deleted;
    Throwable error;

    static FetchResult create(
        GithubIssue result, boolean added, boolean updated, boolean deleted, Throwable error) {
      FetchResultBuilder builder = FetchResult.builder().githubIssue(result);
      if (error != null) {
        builder.error(error);
      } else if (added) {
        builder.added(true);
      } else if (updated) {
        builder.updated(true);
      } else if (deleted) {
        builder.deleted(true);
      }
      return builder.build();
    }
  }

  public Single<FetchResult> fetch(String owner, String repo, int issueNumber) {
    return repository
        .findOne(owner, repo, issueNumber)
        .switchIfEmpty(Single.just(GithubIssue.empty(owner, repo, issueNumber)))
        .flatMap(
            existed -> {
              FetchIssueRequest request =
                  FetchIssueRequest.builder()
                      .owner(owner)
                      .repo(repo)
                      .issueNumber(issueNumber)
                      .etag(existed.getEtag())
                      .build();
              boolean exists = existed.getTimestamp().isAfter(Instant.EPOCH);

              return githubApi
                  .fetchIssue(request)
                  .flatMap(
                      response -> {
                        if (response.getStatus().is2xxSuccessful()) {
                          GithubIssue githubIssue =
                              GithubIssue.builder()
                                  .owner(owner)
                                  .repo(repo)
                                  .issueNumber(issueNumber)
                                  .timestamp(Instant.now())
                                  .etag(response.getEtag())
                                  .data(response.getBody())
                                  .build();
                          return repository
                              .save(githubIssue)
                              .toSingle(
                                  () ->
                                      FetchResult.create(
                                          githubIssue, !exists, exists, false, null));
                        } else if (response.getStatus().value() == 304) {
                          // Not modified
                          return Single.just(
                              FetchResult.create(existed, false, false, false, null));
                        } else if (response.getStatus().value() == 301
                            || response.getStatus().value() == 404
                            || response.getStatus().value() == 410) {
                          // Transferred or deleted
                          return repository
                              .delete(owner, repo, issueNumber)
                              .toSingle(
                                  () -> FetchResult.create(existed, false, false, true, null));
                        } else {
                          log.error(
                              "Failed to fetch {}/{}/issues/{}: {}",
                              owner,
                              repo,
                              issueNumber,
                              response.getStatus().toString());
                          return Single.just(
                              FetchResult.create(
                                  existed,
                                  false,
                                  false,
                                  false,
                                  new IOException(response.getStatus().toString())));
                        }
                      });
            });
  }
}
