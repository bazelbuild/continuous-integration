package build.bazel.dashboard.github.issue;

import build.bazel.dashboard.github.api.FetchIssueRequest;
import build.bazel.dashboard.github.api.GithubApi;
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
    Throwable error;

    static FetchResult create(GithubIssue result, boolean exists, boolean saved, Throwable error) {
      FetchResultBuilder builder = FetchResult.builder().githubIssue(result);
      if (error != null) {
        builder.error(error);
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
                              .toSingle(() -> FetchResult.create(githubIssue, exists, true, null));
                        } else if (response.getStatus().value() == 304) {
                          // Not modified
                          return Single.just(FetchResult.create(existed, exists, false, null));
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
                                  exists,
                                  false,
                                  new IOException(response.getStatus().toString())));
                        }
                      });
            });
  }
}
