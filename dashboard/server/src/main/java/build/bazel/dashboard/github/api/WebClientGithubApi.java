package build.bazel.dashboard.github.api;

import com.google.common.base.Strings;
import io.reactivex.rxjava3.core.Single;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.util.UriComponentsBuilder;
import reactor.adapter.rxjava.RxJava3Adapter;

import java.util.Optional;

import static com.google.common.base.Preconditions.checkNotNull;

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
    checkNotNull(request.getOwner());
    checkNotNull(request.getRepo());

    String url =
        newUrl("repos", request.getOwner(), request.getRepo(), "issues")
            .queryParamIfPresent("per_page", Optional.ofNullable(request.getPerPage()))
            .queryParamIfPresent("page", Optional.ofNullable(request.getPage()))
            .build()
            .toString();

    WebClient.RequestHeadersSpec<?> spec = get(url);

    return exchange(spec);
  }

  @Override
  public Single<GithubApiResponse> listRepositoryEvents(ListRepositoryEventsRequest request) {
    checkNotNull(request.getOwner());
    checkNotNull(request.getRepo());

    log.debug("Listing GitHub repository events: {}", request.toString());

    String url =
        newUrl("repos", request.getOwner(), request.getRepo(), "events")
            .queryParamIfPresent("per_page", Optional.ofNullable(request.getPerPage()))
            .queryParamIfPresent("page", Optional.ofNullable(request.getPage()))
            .build()
            .toString();

    WebClient.RequestHeadersSpec<?> spec = get(url);
    if (!Strings.isNullOrEmpty(request.getEtag())) {
      spec.ifNoneMatch(request.getEtag());
    }

    return exchange(spec);
  }

  @Override
  public Single<GithubApiResponse> fetchIssue(FetchIssueRequest request) {
    checkNotNull(request.getOwner());
    checkNotNull(request.getRepo());

    log.debug("Fetching GitHub issue: {}", request);

    String url =
        newUrl(
            "repos",
            request.getOwner(),
            request.getRepo(),
            "issues",
            String.valueOf(request.getIssueNumber()))
            .build()
            .toString();

    WebClient.RequestHeadersSpec<?> spec = get(url);
    if (!Strings.isNullOrEmpty(request.getEtag())) {
      spec.ifNoneMatch(request.getEtag());
    }

    return exchange(spec);
  }

  private UriComponentsBuilder newUrl(String... pathSegment) {
    return UriComponentsBuilder.newInstance().scheme(SCHEME).host(HOST).pathSegment(pathSegment);
  }

  private WebClient.RequestHeadersSpec<?> get(String url) {
    WebClient.RequestHeadersSpec<?> spec =
        webClient.get().uri(url).header("Accept", "application/vnd.github.v3+json");

    if (!Strings.isNullOrEmpty(accessToken)) {
      spec = spec.header("Authorization", "token " + accessToken);
    }

    return spec;
  }

  private Single<GithubApiResponse> exchange(WebClient.RequestHeadersSpec<?> spec) {
    return RxJava3Adapter.monoToSingle(spec.exchangeToMono(GithubApiResponse::fromClientResponse));
  }
}
