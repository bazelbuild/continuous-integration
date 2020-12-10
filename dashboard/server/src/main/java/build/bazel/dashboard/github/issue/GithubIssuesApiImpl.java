package build.bazel.dashboard.github.issue;

import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.util.UriComponentsBuilder;
import reactor.core.publisher.Mono;

import java.io.IOException;

@Component
public class GithubIssuesApiImpl implements GithubIssuesApi {

  private final WebClient webClient;

  public GithubIssuesApiImpl(WebClient webClient) {
    this.webClient = webClient;
  }

  @Override
  public Mono<JsonNode> listRepositoryIssues(ListRepositoryIssuesRequest request) {
    String url =
        UriComponentsBuilder.newInstance()
            .scheme("https")
            .host("api.github.com")
            .pathSegment("repos", request.getOwner(), request.getRepo(), "issues")
            .queryParam("per_page", request.getPerPage())
            .queryParam("page", request.getPage())
            .build()
            .toString();

    return webClient
        .get()
        .uri(url)
        .header("accept", "application/vnd.github.v3+json")
        .exchangeToMono(
            clientResponse -> {
              if (clientResponse.statusCode().is2xxSuccessful()) {
                return clientResponse.bodyToMono(JsonNode.class);
              }
              return Mono.error(new IOException(clientResponse.statusCode().toString()));
            });
  }
}
