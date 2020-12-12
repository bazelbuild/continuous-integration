package build.bazel.dashboard.github.api;

import com.google.common.base.Strings;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.util.UriComponentsBuilder;
import reactor.core.publisher.Mono;

import static com.google.common.base.Preconditions.checkNotNull;

@Component
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
  public Mono<GithubApiResponse> listRepositoryIssues(ListRepositoryIssuesRequest request) {
    checkNotNull(request.getOwner());
    checkNotNull(request.getRepo());

    String url =
        UriComponentsBuilder.newInstance()
            .scheme(SCHEME)
            .host(HOST)
            .pathSegment("repos", request.getOwner(), request.getRepo(), "issues")
            .queryParam("per_page", request.getPerPage())
            .queryParam("page", request.getPage())
            .build()
            .toString();

    return webClient
        .get()
        .uri(url)
        .header("accept", "application/vnd.github.v3+json")
        .exchangeToMono(GithubApiResponse::fromClientResponse);
  }

  @Override
  public Mono<GithubApiResponse> getIssue(GetIssueRequest request) {
    checkNotNull(request.getOwner());
    checkNotNull(request.getRepo());

    String url =
        UriComponentsBuilder.newInstance()
            .scheme(SCHEME)
            .host(HOST)
            .pathSegment(
                "repos",
                request.getOwner(),
                request.getRepo(),
                "issues",
                String.valueOf(request.getIssueNumber()))
            .build()
            .toString();
    WebClient.RequestHeadersSpec<?> spec = get(url);

    if (!Strings.isNullOrEmpty(request.getETag())) {
      spec.ifNoneMatch(request.getETag());
    }

    return spec.exchangeToMono(GithubApiResponse::fromClientResponse);
  }

  private WebClient.RequestHeadersSpec<?> get(String url) {
    WebClient.RequestHeadersSpec<?> spec =
        webClient.get().uri(url).header("Accept", "application/vnd.github.v3+json");

    if (!Strings.isNullOrEmpty(accessToken)) {
      spec = spec.header("Authorization", "token " + accessToken);
    }

    return spec;
  }
}
