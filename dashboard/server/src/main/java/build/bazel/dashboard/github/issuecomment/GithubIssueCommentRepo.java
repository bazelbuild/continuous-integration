package build.bazel.dashboard.github.issuecomment;

import com.fasterxml.jackson.databind.JsonNode;
import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Maybe;
import java.time.Instant;
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

  Maybe<GithubIssueCommentPage> findOnePage(String owner, String repo, int issueNumber, int page);

  Flowable<GithubIssueCommentPage> findAllPages(String owner, String repo, int issueNumber);

  Completable savePage(GithubIssueCommentPage page);
}
