package build.bazel.dashboard.github.api;

import static com.google.common.base.Preconditions.checkNotNull;

import com.google.common.base.Strings;
import java.net.URI;
import java.util.Optional;
import java.util.function.Function;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.util.UriBuilder;

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
  public GithubApiResponse listRepositoryIssues(ListRepositoryIssuesRequest request) {
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
                    .build(), "");

    return exchange(spec);
  }

  @Override
  public GithubApiResponse listRepositoryEvents(ListRepositoryEventsRequest request) {
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
                    .build(), request.getEtag());

    return exchange(spec);
  }

  @Override
  public GithubApiResponse listRepositoryIssueEvents(ListRepositoryIssueEventsRequest request) {
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
                    .build(), request.getEtag());

    return exchange(spec);
  }

  @Override
  public GithubApiResponse fetchIssue(FetchIssueRequest request) {
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
                    .build(), request.getEtag());

    return exchange(spec);
  }

  @Override
  public GithubApiResponse listIssueComments(ListIssueCommentsRequest request) {
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
                        Integer.toString(request.getIssueNumber()),
                        "comments")
                    .queryParamIfPresent("per_page", Optional.ofNullable(request.getPerPage()))
                    .queryParamIfPresent("page", Optional.ofNullable(request.getPage()))
                    .build(), request.getEtag());

    return exchange(spec);
  }

  @Override
  public GithubApiResponse searchIssues(SearchIssuesRequest request) {
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
                    .build(request.getQ()), "");

    return exchange(spec);
  }

  private WebClient.RequestHeadersSpec<?> get(Function<UriBuilder, URI> uriFunction, String etag) {
    WebClient.RequestHeadersSpec<?> spec =
        webClient
            .get()
            .uri(uriBuilder -> uriFunction.apply(uriBuilder.scheme(SCHEME).host(HOST)))
            .header("Accept", "application/vnd.github.v3+json");

    if (!Strings.isNullOrEmpty(etag)) {
      spec.ifNoneMatch(etag);
    }

    spec.headers(headers -> log.debug("{}", headers.toSingleValueMap()));

    if (!Strings.isNullOrEmpty(accessToken)) {
      spec = spec.header("Authorization", "token " + accessToken);
    }

    return spec;
  }

  private GithubApiResponse exchange(WebClient.RequestHeadersSpec<?> spec) {
    return spec.exchangeToMono(response -> {
      log.debug("{} {}", response.statusCode(), response.headers().asHttpHeaders().toSingleValueMap());
      return GithubApiResponse.fromClientResponse(response);
    }).block();
  }
}
