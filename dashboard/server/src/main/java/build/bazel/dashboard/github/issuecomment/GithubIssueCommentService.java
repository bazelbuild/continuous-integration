package build.bazel.dashboard.github.issuecomment;

import build.bazel.dashboard.github.api.GithubApi;
import build.bazel.dashboard.github.api.ListIssueCommentsRequest;
import build.bazel.dashboard.github.issuecomment.GithubIssueCommentRepo.GithubIssueCommentPage;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.reactivex.rxjava3.core.Flowable;
import java.io.IOException;
import java.time.Instant;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class GithubIssueCommentService {
  private static final int PER_PAGE = 100;

  private final GithubIssueCommentRepo githubIssueCommentRepo;
  private final GithubApi githubApi;
  private final ObjectMapper objectMapper;

  public Flowable<GithubComment> findIssueComments(String owner, String repo, int issueNumber) {
    return githubIssueCommentRepo
        .findAllPages(owner, repo, issueNumber)
        .concatMap(page -> Flowable.fromIterable(page.getData()))
        .map(jsonNode -> objectMapper.treeToValue(jsonNode, GithubComment.class));
  }

  public void syncIssueComments(String owner, String repo, int issueNumber) {
    int page = 1;
    while (true) {
      try {
        var node = syncIssueCommentPage(owner, repo, issueNumber, page);
        if (node.size() < PER_PAGE) {
          break;
        }
      } catch (IOException e) {
        log.error("Failed to sync issue comments: " + e.getMessage(), e);
        return;
      }
    }
  }

  private JsonNode syncIssueCommentPage(String owner, String repo, int issueNumber, int page)
      throws IOException {
    var existedPage = githubIssueCommentRepo.findOnePage(owner, repo, issueNumber, page);
    var existedEtag = existedPage.map(GithubIssueCommentPage::getEtag).orElse("");
    var request =
        ListIssueCommentsRequest.builder()
            .owner(owner)
            .repo(repo)
            .issueNumber(issueNumber)
            .perPage(PER_PAGE)
            .page(page)
            .etag(existedEtag)
            .build();
    var response = githubApi.listIssueComments(request);
    if (response.getStatus().is2xxSuccessful()) {
      githubIssueCommentRepo.savePage(
          GithubIssueCommentPage.builder()
              .owner(owner)
              .repo(repo)
              .issueNumber(issueNumber)
              .page(page)
              .timestamp(Instant.now())
              .etag(response.getEtag())
              .data(response.getBody())
              .build());
      return response.getBody();
    } else if (response.getStatus().value() == 304) {
      // Not modified
      if (existedPage.isPresent()) {
        return existedPage.get().getData();
      }
      return objectMapper.createArrayNode();
    } else {
      throw new IOException(response.getStatus().toString());
    }
  }
}
