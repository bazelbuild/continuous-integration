package build.bazel.dashboard.github.issue;

import build.bazel.dashboard.github.api.FetchIssueRequest;
import build.bazel.dashboard.github.api.FetchPullRequestRequest;
import build.bazel.dashboard.github.api.GithubApi;
import build.bazel.dashboard.github.issuestatus.GithubIssueStatus;
import build.bazel.dashboard.github.issuestatus.GithubIssueStatusService;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.time.Instant;
import java.util.Optional;
import javax.annotation.Nullable;
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
  private final GithubPullRequestRepo githubPullRequestRepo;
  private final GithubIssueStatusService githubIssueStatusService;
  private final ObjectMapper objectMapper;

  @Builder
  @Value
  public static class FetchResult {
    GithubIssue issue;
    @Nullable GithubPullRequest pullRequest;
    GithubIssueStatus status;
    boolean added;
    boolean updated;
    boolean deleted;
    Throwable error;

    static FetchResult create(
        GithubIssue result,
        GithubPullRequest pullRequest,
        GithubIssueStatus status,
        boolean added,
        boolean updated,
        boolean deleted,
        Throwable error) {
      FetchResultBuilder builder = FetchResult.builder().issue(result).status(status);
      if (pullRequest != null) {
        builder.pullRequest(pullRequest);
      }
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
            .orElse(GithubIssue.empty(owner, repo, issueNumber, objectMapper));

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
        var pullRequest = fetchAndSavePullRequest(githubIssue);
        var status = githubIssueStatusService.check(githubIssue, pullRequest, Instant.now());
        return FetchResult.create(
            githubIssue, pullRequest, status.orElse(null), !exists, exists, false, null);
      } catch (IOException e) {
        return FetchResult.create(githubIssue, null, null, !exists, exists, false, e);
      }
    } else if (response.getStatus().value() == 304) {
      // Not modified
      try {
        var pullRequest = fetchAndSavePullRequest(existed);
        var status = githubIssueStatusService.check(existed, pullRequest, Instant.now());
        return FetchResult.create(
            existed, pullRequest, status.orElse(null), false, false, false, null);
      } catch (IOException e) {
        return FetchResult.create(existed, null, null, false, false, false, e);
      }
    } else if (response.getStatus().value() == 301
        || response.getStatus().value() == 404
        || response.getStatus().value() == 410) {
      // Transferred or deleted
      githubIssueRepo.delete(owner, repo, issueNumber);
      githubPullRequestRepo.delete(owner, repo, issueNumber);
      // Mark existing status to DELETED
      githubIssueStatusService.markDeleted(owner, repo, issueNumber);
      return FetchResult.create(existed, null, null, false, false, true, null);
    } else {
      log.error(
          "Failed to fetch {}/{}/issues/{}: {}",
          owner,
          repo,
          issueNumber,
          response.getStatus().toString());
      return FetchResult.create(
          existed,
          null,
          null,
          false,
          false,
          false,
          new IOException(response.getStatus().toString()));
    }
  }

  public Integer findMaxIssueNumber(String owner, String repo) {
    return githubIssueRepo.findMaxIssueNumber(owner, repo);
  }

  @Nullable
  private GithubPullRequest fetchAndSavePullRequest(GithubIssue issue) throws IOException {
    if (!issue.parseData(objectMapper).isPullRequest()) {
      return null;
    }

    var existed =
        githubPullRequestRepo
            .findOne(issue.getOwner(), issue.getRepo(), issue.getIssueNumber())
            .orElse(
                GithubPullRequest.empty(
                    issue.getOwner(), issue.getRepo(), issue.getIssueNumber(), objectMapper));

    var request =
        new FetchPullRequestRequest(
            existed.owner(), existed.repo(), existed.issueNumber(), existed.etag());

    var response = githubApi.fetchPullRequest(request);
    if (response.getStatus().is2xxSuccessful()) {
      var pullRequest =
          new GithubPullRequest(
              existed.owner(),
              existed.repo(),
              existed.issueNumber(),
              Instant.now(),
              response.getEtag(),
              response.getBody());
      githubPullRequestRepo.save(pullRequest);
      return pullRequest;
    } else if (response.getStatus().value() == 304) {
      // Not modified
      return existed;
    } else {
      throw new IOException(
          String.format(
              "Failed to fetch %s/%s/pulls/%s: %s",
              existed.owner(), existed.repo(), existed.issueNumber(), response.getStatus()));
    }
  }
}
