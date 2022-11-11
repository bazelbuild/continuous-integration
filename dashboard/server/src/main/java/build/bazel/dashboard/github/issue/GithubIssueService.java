package build.bazel.dashboard.github.issue;

import build.bazel.dashboard.github.api.FetchIssueRequest;
import build.bazel.dashboard.github.api.GithubApi;
import build.bazel.dashboard.github.issuestatus.GithubIssueStatus;
import build.bazel.dashboard.github.issuestatus.GithubIssueStatusService;
import java.io.IOException;
import java.time.Instant;
import java.util.Optional;
import lombok.Builder;
import lombok.RequiredArgsConstructor;
import lombok.Value;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Service
@Slf4j
@RequiredArgsConstructor
public class GithubIssueService {

  private final GithubApi githubApi;
  private final GithubIssueRepo githubIssueRepo;
  private final GithubIssueStatusService githubIssueStatusService;

  @Builder
  @Value
  public static class FetchResult {
    GithubIssue issue;
    GithubIssueStatus status;
    boolean added;
    boolean updated;
    boolean deleted;
    Throwable error;

    static FetchResult create(
        GithubIssue result, GithubIssueStatus status, boolean added, boolean updated, boolean deleted, Throwable error) {
      FetchResultBuilder builder = FetchResult.builder().issue(result).status(status);
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

  public Optional<GithubIssue> findOne(String owner, String repo, int issueNumber) {
    return githubIssueRepo.findOne(owner, repo, issueNumber);
  }

  public FetchResult fetchAndSave(String owner, String repo, int issueNumber) {
    var existed =
        githubIssueRepo
            .findOne(owner, repo, issueNumber)
            .orElse(GithubIssue.empty(owner, repo, issueNumber));

    FetchIssueRequest request =
        FetchIssueRequest.builder()
            .owner(owner)
            .repo(repo)
            .issueNumber(issueNumber)
            .etag(existed.getEtag())
            .build();
    boolean exists = existed.getTimestamp().isAfter(Instant.EPOCH);
    var response = githubApi.fetchIssue(request);
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
      try {
        githubIssueRepo.save(githubIssue);
        var status = githubIssueStatusService.check(githubIssue, Instant.now());
        return FetchResult.create(githubIssue, status.orElse(null), !exists, exists, false, null);
      } catch (IOException e) {
        return FetchResult.create(githubIssue, null, !exists, exists, false, e);
      }
    } else if (response.getStatus().value() == 304) {
      // Not modified
      try {
        var status = githubIssueStatusService.check(existed, Instant.now());
        return FetchResult.create(existed, status.orElse(null), false, false, false, null);
      } catch (IOException e) {
        return FetchResult.create(existed, null, false, false, false, e);
      }
    } else if (response.getStatus().value() == 301
        || response.getStatus().value() == 404
        || response.getStatus().value() == 410) {
      // Transferred or deleted
      githubIssueRepo.delete(owner, repo, issueNumber);
      // Mark existing status to DELETED
      githubIssueStatusService.markDeleted(owner, repo, issueNumber);
      return FetchResult.create(existed, null, false, false, true, null);
    } else {
      log.error(
          "Failed to fetch {}/{}/issues/{}: {}",
          owner,
          repo,
          issueNumber,
          response.getStatus().toString());
      return FetchResult.create(
          existed, null, false, false, false, new IOException(response.getStatus().toString()));
    }
  }

  public Integer findMaxIssueNumber(String owner, String repo) {
    return githubIssueRepo.findMaxIssueNumber(owner, repo);
  }
}
