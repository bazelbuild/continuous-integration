package build.bazel.dashboard.github.issue;

import build.bazel.dashboard.github.api.GithubApi;
import build.bazel.dashboard.github.api.SearchIssuesRequest;
import io.reactivex.rxjava3.core.Single;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import java.io.IOException;

@Slf4j
@RequiredArgsConstructor
public class GithubApiSearchExecutor implements GithubSearchExecutor {
  private final GithubApi githubApi;

  @Override
  public Single<Integer> fetchSearchResultCount(String owner, String repo, String query) {
    SearchIssuesRequest request =
        SearchIssuesRequest.builder().q(String.format("repo:%s/%s %s", owner, repo, query)).build();
    return githubApi
        .searchIssues(request)
        .flatMap(
            response -> {
              if (response.getStatus().is2xxSuccessful()) {
                return Single.just(response.getBody().get("total_count").asInt());
              } else {
                return Single.error(new IOException(response.getStatus().toString()));
              }
            });
  }
}
