package build.bazel.dashboard.github.issuelist;

import build.bazel.dashboard.github.issuestatus.GithubIssueStatus;
import io.reactivex.rxjava3.core.Single;
import lombok.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Nullable;

@Service
@Slf4j
@RequiredArgsConstructor
public class GithubIssueListService {

  private final GithubIssueListRepo githubIssueListRepo;

  @NoArgsConstructor
  @Data
  public static class ListParams {
    @Nullable GithubIssueStatus.Status status;
  }

  public Single<GithubIssueList> find(String owner, String repo, ListParams params) {
    return githubIssueListRepo.find(owner, repo, params);
  }
}
