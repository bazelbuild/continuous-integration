package build.bazel.dashboard.github.issuecomment;

import com.fasterxml.jackson.databind.JsonNode;
import io.reactivex.rxjava3.core.Flowable;
import java.time.Instant;
import java.util.Optional;
import lombok.Builder;
import lombok.Data;

public interface GithubIssueCommentRepo {
  @Builder
  @Data
  class GithubIssueCommentPage {
    String owner;
    String repo;
    int issueNumber;
    int page;
    Instant timestamp;
    String etag;
    JsonNode data;
  }

  Optional<GithubIssueCommentPage> findOnePage(String owner, String repo, int issueNumber, int page);

  Flowable<GithubIssueCommentPage> findAllPages(String owner, String repo, int issueNumber);

  void savePage(GithubIssueCommentPage page);
}
