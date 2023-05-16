package build.bazel.dashboard.github.api;

import static com.google.common.base.Preconditions.checkNotNull;

import build.bazel.dashboard.common.RestApiClient;
import build.bazel.dashboard.common.RestApiResponse;
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
public class WebClientGithubApi extends RestApiClient implements GithubApi {
  private final String accessToken;

  public WebClientGithubApi(
      WebClient webClient, @Value("${github.accessToken:}") String accessToken) {
    super("https", "api.github.com", webClient);
    this.accessToken = accessToken;
  }

  @Override
  public RestApiResponse listRepositoryIssues(ListRepositoryIssuesRequest request) {
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
  public RestApiResponse listRepositoryEvents(ListRepositoryEventsRequest request) {
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
  public RestApiResponse listRepositoryIssueEvents(ListRepositoryIssueEventsRequest request) {
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
  public RestApiResponse fetchIssue(FetchIssueRequest request) {
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
  public RestApiResponse listIssueComments(ListIssueCommentsRequest request) {
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
  public RestApiResponse searchIssues(SearchIssuesRequest request) {
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

  @Override
  protected WebClient.RequestHeadersSpec<?> get(Function<UriBuilder, URI> uriFunction, String etag) {
    var spec = super.get(uriFunction, etag);
    spec.header("Accept", "application/vnd.github.v3+json");
    if (!Strings.isNullOrEmpty(accessToken)) {
      spec.header("Authorization", "token " + accessToken);
    }
    return spec;
  }
}
