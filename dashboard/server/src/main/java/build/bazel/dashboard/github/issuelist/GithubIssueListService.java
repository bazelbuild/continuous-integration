package build.bazel.dashboard.github.issuelist;

import build.bazel.dashboard.github.issuestatus.GithubIssueStatus;
import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Single;
import lombok.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Nullable;
import java.util.List;
import java.util.stream.Collectors;

@Service
@Slf4j
@RequiredArgsConstructor
public class GithubIssueListService {

  private final GithubIssueListRepo githubIssueListRepo;

  @NoArgsConstructor
  @Data
  public static class ListParams {
    @Nullable String owner;
    @Nullable String repo;
    @Nullable Boolean isPullRequest;
    @Nullable GithubIssueStatus.Status status;
    @Nullable Integer page;
    @Nullable Integer pageSize;
    @Nullable String actionOwner;
    @Nullable ListSortParams sort;
    @Nullable List<String> labels;
  }

  public enum ListSortParams {
    EXPECTED_RESPOND_AT_ASC,
    EXPECTED_RESPOND_AT_DESC,
  }

  public Single<GithubIssueList> find(ListParams params) {
    if (params.page == null) {
      params.page = 1;
    }
    if (params.page < 1) {
      params.page = 1;
    }

    if (params.pageSize == null) {
      params.pageSize = 10;
    }
    params.pageSize = Math.min(params.pageSize, 100);

    return githubIssueListRepo
        .find(params)
        .collect(Collectors.toList())
        .flatMap(
            items ->
                githubIssueListRepo
                    .count(params)
                    .map(
                        total ->
                            GithubIssueList.builder()
                                .items(items)
                                .total(total)
                                .page(params.page)
                                .pageSize(params.pageSize)
                                .build()));
  }

  public Flowable<String> findAllActionOwner(ListParams params) {
    return githubIssueListRepo.findAllActionOwner(params);
  }
}