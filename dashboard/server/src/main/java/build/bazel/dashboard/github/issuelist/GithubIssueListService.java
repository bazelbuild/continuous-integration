package build.bazel.dashboard.github.issuelist;

import build.bazel.dashboard.github.issuestatus.GithubIssueStatus;
import io.reactivex.rxjava3.core.Single;
import lombok.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Nullable;
import java.util.stream.Collectors;

@Service
@Slf4j
@RequiredArgsConstructor
public class GithubIssueListService {

  private final GithubIssueListRepo githubIssueListRepo;

  @NoArgsConstructor
  @Data
  public static class ListParams {
    @Nullable Boolean isPullRequest;
    @Nullable GithubIssueStatus.Status status;
    @Nullable Integer page;
    @Nullable String actionOwner;
    @Nullable ListSortParams sort;
  }

  public enum ListSortParams {
    EXPECTED_RESPOND_AT_ASC,
    EXPECTED_RESPOND_AT_DESC,
  }

  public Single<GithubIssueList> find(String owner, String repo, ListParams params) {
    return githubIssueListRepo
        .find(owner, repo, params)
        .collect(Collectors.toList())
        .flatMap(
            items ->
                githubIssueListRepo
                    .count(owner, repo, params)
                    .map(total -> GithubIssueList.builder().items(items).total(total).build()));
  }
}
