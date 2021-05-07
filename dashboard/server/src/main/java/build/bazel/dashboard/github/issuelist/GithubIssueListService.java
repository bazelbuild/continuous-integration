package build.bazel.dashboard.github.issuelist;

import io.reactivex.rxjava3.core.Single;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Service
@Slf4j
@RequiredArgsConstructor
public class GithubIssueListService {

  private final GithubIssueListRepo githubIssueListRepo;

  public Single<GithubIssueList> find(String owner, String repo) {
    return githubIssueListRepo.find(owner, repo);
  }
}
