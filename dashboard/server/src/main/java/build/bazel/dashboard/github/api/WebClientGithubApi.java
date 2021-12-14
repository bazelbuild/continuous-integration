package build.bazel.dashboard.github.api;

import com.google.common.base.Strings;
import io.reactivex.rxjava3.core.Single;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.util.UriBuilder;
import reactor.adapter.rxjava.RxJava3Adapter;

import java.net.URI;
import java.util.Optional;
import java.util.function.Function;

import static com.google.common.base.Preconditions.checkNotNull;
import static java.nio.charset.StandardCharsets.UTF_8;

@Component
@Slf4j
public class WebClientGithubApi implements GithubApi {
  private static final String SCHEME = "https";
  private static final String HOST = "api.github.com";

  private final WebClient webClient;
  private final String accessToken;

  public WebClientGithubApi(
      WebClient webClient, @Value("${github.accessToken:}") String accessToken) {
    this.webClient = webClient;
    this.accessToken = accessToken;
  }

  @Override
  public Single<GithubApiResponse> listRepositoryIssues(ListRepositoryIssuesRequest request) {
    log.debug("{}", request);

    checkNotNull(request.getOwner());
    checkNotNull(request.getRepo());

    WebClient.RequestHeadersSpec<?> spec =
        get(
            uriBuilder ->
                uriBuilder
                    .pathSegment("repos", request.getOwner(), request.getRepo(), "issues")
                    .queryParamIfPresent("per_page", Optional.ofNullable(request.getPerPage()))
                    .queryParamIfPresent("page", Optional.ofNullable(request.getPage()))
                    .build());

    return exchange(spec);
  }

  @Override
  public Single<GithubApiResponse> listRepositoryEvents(ListRepositoryEventsRequest request) {
    log.debug("{}", request);

    checkNotNull(request.getOwner());
    checkNotNull(request.getRepo());

    WebClient.RequestHeadersSpec<?> spec =
        get(
            uriBuilder ->
                uriBuilder
                    .pathSegment("repos", request.getOwner(), request.getRepo(), "events")
                    .queryParamIfPresent("per_page", Optional.ofNullable(request.getPerPage()))
                    .queryParamIfPresent("page", Optional.ofNullable(request.getPage()))
                    .build());
    if (!Strings.isNullOrEmpty(request.getEtag())) {
      spec.ifNoneMatch(request.getEtag());
    }

    return exchange(spec);
  }

  @Override
  public Single<GithubApiResponse> listRepositoryIssueEvents(ListRepositoryIssueEventsRequest request) {
    log.debug("{}", request);

    checkNotNull(request.getOwner());
    checkNotNull(request.getRepo());

    WebClient.RequestHeadersSpec<?> spec =
        get(
            uriBuilder ->
                uriBuilder
                    .pathSegment("repos", request.getOwner(), request.getRepo(), "issues", "events")
                    .queryParamIfPresent("per_page", Optional.ofNullable(request.getPerPage()))
                    .queryParamIfPresent("page", Optional.ofNullable(request.getPage()))
                    .build());
    if (!Strings.isNullOrEmpty(request.getEtag())) {
      spec.ifNoneMatch(request.getEtag());
    }

    return exchange(spec);
  }

  @Override
  public Single<GithubApiResponse> fetchIssue(FetchIssueRequest request) {
    log.debug("{}", request);

    checkNotNull(request.getOwner());
    checkNotNull(request.getRepo());

    WebClient.RequestHeadersSpec<?> spec =
        get(
            uriBuilder ->
                uriBuilder
                    .pathSegment(
                        "repos",
                        request.getOwner(),
                        request.getRepo(),
                        "issues",
                        String.valueOf(request.getIssueNumber()))
                    .build());
    if (!Strings.isNullOrEmpty(request.getEtag())) {
      spec.ifNoneMatch(request.getEtag());
    }

    return exchange(spec);
  }

  @Override
  public Single<GithubApiResponse> listIssueComments(ListIssueCommentsRequest request) {
    log.debug("{}", request);

    checkNotNull(request.getOwner());
    checkNotNull(request.getRepo());

    WebClient.RequestHeadersSpec<?> spec =
        get(
            uriBuilder ->
                uriBuilder
                    .pathSegment("repos", request.getOwner(), request.getRepo(), "issues", Integer.toString(request.getIssueNumber()), "comments")
                    .queryParamIfPresent("per_page", Optional.ofNullable(request.getPerPage()))
                    .queryParamIfPresent("page", Optional.ofNullable(request.getPage()))
                    .build());
    if (!Strings.isNullOrEmpty(request.getEtag())) {
      spec.ifNoneMatch(request.getEtag());
    }

    return exchange(spec);
  }

  @Override
  public Single<GithubApiResponse> searchIssues(SearchIssuesRequest request) {
    log.debug("{}", request);

    checkNotNull(request.getQ());

    WebClient.RequestHeadersSpec<?> spec =
        get(
            uriBuilder ->
                uriBuilder
                    .pathSegment("search", "issues")
                    .queryParam("q", "{query}")
                    .queryParamIfPresent("sort", Optional.ofNullable(request.getSort()))
                    .queryParamIfPresent("order", Optional.ofNullable(request.getOrder()))
                    .queryParamIfPresent("per_page", Optional.ofNullable(request.getPerPage()))
                    .queryParamIfPresent("page", Optional.ofNullable(request.getPage()))
                    .build(request.getQ()));

    return exchange(spec);
  }

  private WebClient.RequestHeadersSpec<?> get(Function<UriBuilder, URI> uriFunction) {
    WebClient.RequestHeadersSpec<?> spec =
        webClient
            .get()
            .uri(uriBuilder -> uriFunction.apply(uriBuilder.scheme(SCHEME).host(HOST)))
            .header("Accept", "application/vnd.github.v3+json");

    if (!Strings.isNullOrEmpty(accessToken)) {
      spec = spec.header("Authorization", "token " + accessToken);
    }

    return spec;
  }

  private Single<GithubApiResponse> exchange(WebClient.RequestHeadersSpec<?> spec) {
    return RxJava3Adapter.monoToSingle(spec.exchangeToMono(GithubApiResponse::fromClientResponse));
  }
}
