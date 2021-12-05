package build.bazel.dashboard.github.issuecomment;

import build.bazel.dashboard.github.api.GithubApi;
import build.bazel.dashboard.github.api.ListIssueCommentsRequest;
import build.bazel.dashboard.github.issuecomment.GithubIssueCommentRepo.GithubIssueCommentPage;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Single;
import java.io.IOException;
import java.time.Instant;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
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

  public Completable syncIssueComments(String owner, String repo, int issueNumber) {
    Flowable<Integer> pages =
        Flowable.generate(
            AtomicInteger::new,
            (state, emitter) -> {
              emitter.onNext(state.incrementAndGet());
            });

    return Completable.fromPublisher(
        pages
            .flatMapSingle(page -> syncIssueCommentPage(owner, repo, issueNumber, page), false, 1)
            .takeUntil(node -> node.size() < PER_PAGE));
  }

  private Single<JsonNode> syncIssueCommentPage(
      String owner, String repo, int issueNumber, int page) {
    AtomicReference<GithubIssueCommentPage> existedPage = new AtomicReference<>();
    return githubIssueCommentRepo
        .findOnePage(owner, repo, issueNumber, page)
        .doOnSuccess(existedPage::set)
        .map(GithubIssueCommentPage::getEtag)
        .defaultIfEmpty("")
        .map(
            etag ->
                ListIssueCommentsRequest.builder()
                    .owner(owner)
                    .repo(repo)
                    .issueNumber(issueNumber)
                    .perPage(PER_PAGE)
                    .page(page)
                    .etag(etag)
                    .build())
        .flatMap(githubApi::listIssueComments)
        .flatMap(
            response -> {
              if (response.getStatus().is2xxSuccessful()) {
                String etag = response.getEtag();
                return githubIssueCommentRepo
                    .savePage(
                        GithubIssueCommentPage.builder()
                            .owner(owner)
                            .repo(repo)
                            .issueNumber(issueNumber)
                            .page(page)
                            .timestamp(Instant.now())
                            .etag(etag)
                            .data(response.getBody())
                            .build())
                    .andThen(Single.just(response.getBody()));
              } else if (response.getStatus().value() == 304) {
                // Not modified
                GithubIssueCommentPage existed = existedPage.get();
                if (existed == null) {
                  return Single.just(objectMapper.createArrayNode());
                }
                return Single.just(existed.getData());
              } else {
                return Single.error(new IOException(response.getStatus().toString()));
              }
            });
  }
}
