package build.bazel.dashboard.github.issuequery.task;

import build.bazel.dashboard.github.issuequery.task.GithubIssueQueryCountTaskResult;
import build.bazel.dashboard.github.GithubUtils;
import build.bazel.dashboard.github.issuequery.task.GithubIssueQueryCountTaskRepo;
import build.bazel.dashboard.github.issuequery.GithubIssueQueryRepo;
import build.bazel.dashboard.utils.Period;
import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Maybe;
import lombok.Builder;
import lombok.RequiredArgsConstructor;
import lombok.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequiredArgsConstructor
public class GithubIssueQueryCountTaskRestController {
  private final GithubIssueQueryRepo githubIssueQueryRepo;
  private final GithubIssueQueryCountTaskRepo githubIssueQueryCountTaskRepo;

  @Builder
  @Value
  static class CountResult {
    String id;
    String name;
    String url;
    List<CountResultItem> items;
  }

  @Builder
  @Value
  static class CountResultItem {
    Instant timestamp;
    Integer count;
  }

  @GetMapping("/github/{owner}/{repo}/search/count/{queryId}")
  public Maybe<CountResult> fetchCountResult(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @PathVariable("queryId") String queryId,
      @RequestParam("period") Period period,
      @RequestParam(value = "from", required = false) Instant requestFrom,
      @RequestParam(value = "to", required = false) Instant requestTo) {
    if (requestTo == null) {
      requestTo = Instant.now();
    }

    if (requestFrom == null) {
      requestFrom = period.prev(requestTo, 30);
    }

    Instant from = requestFrom;
    Instant to = requestTo;

    return githubIssueQueryRepo
        .findOne(owner, repo, queryId)
        .flatMapSingle(
            query ->
                githubIssueQueryCountTaskRepo
                    .listResult(query.getOwner(), query.getRepo(), query.getId(), period, from, to)
                    .collect(
                        Collectors.toMap(GithubIssueQueryCountTaskResult::getTimestamp, it -> it))
                    .map(
                        resultMap -> {
                          Instant end = period.truncate(to);
                          List<CountResultItem> items = new ArrayList<>();
                          for (Instant timestamp = period.truncate(from);
                               !timestamp.isAfter(end);
                               timestamp = period.next(timestamp)) {
                            Integer count = null;
                            GithubIssueQueryCountTaskResult result = resultMap.get(timestamp);
                            if (result != null) {
                              count = result.getCount();
                            }
                            CountResultItem item =
                                CountResultItem.builder().timestamp(timestamp).count(count).build();
                            items.add(item);
                          }
                          return CountResult.builder()
                              .id(query.getId())
                              .name(query.getName())
                              .url(
                                  GithubUtils.buildIssueQueryUrl(
                                      query.getOwner(), query.getRepo(), query.getQuery()))
                              .items(items)
                              .build();
                        }));
  }

  @GetMapping("/github/{owner}/{repo}/search/count")
  public Flowable<CountResult> fetchCountResults(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @RequestParam("period") Period period,
      @RequestParam("queryId") List<String> queryIds,
      @RequestParam(value = "from", required = false) Instant from,
      @RequestParam(value = "to", required = false) Instant to) {
    return Flowable.fromIterable(queryIds)
        .flatMapMaybe(queryId -> fetchCountResult(owner, repo, queryId, period, from, to));
  }
}