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

import static java.util.Objects.requireNonNull;

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

  private void preprocessParams(ListParams params) {
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
  }

  public Single<GithubIssueList> find(ListParams params) {
    preprocessParams(params);
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
                                .page(requireNonNull(params.getPage()))
                                .pageSize(requireNonNull(params.getPageSize()))
                                .build()));
  }

  public Flowable<String> findAllActionOwner(ListParams params) {
    preprocessParams(params);
    return githubIssueListRepo.findAllActionOwner(params);
  }

  public Flowable<String> findAllLabels(ListParams params) {
    preprocessParams(params);
    return githubIssueListRepo.findAllLabels(params);
  }
}
