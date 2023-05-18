package build.bazel.dashboard.common;

import com.google.common.base.Strings;
import java.net.URI;
import java.util.function.Function;
import javax.annotation.Nullable;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.util.UriBuilder;

@Slf4j
public abstract class RestApiClient {
  protected final String scheme;
  protected final String host;
  protected final WebClient webClient;

  protected RestApiClient(String scheme, String host, WebClient webClient) {
    this.scheme = scheme;
    this.host = host;
    this.webClient = webClient;
  }

  protected WebClient.RequestHeadersSpec<?> get(Function<UriBuilder, URI> uriFunction, @Nullable String etag) {
    var spec =
        webClient
            .get()
            .uri(uriBuilder -> uriFunction.apply(uriBuilder.scheme(scheme).host(host)));

    if (!Strings.isNullOrEmpty(etag)) {
      spec.ifNoneMatch(etag);
    }

    return spec;
  }

  protected RestApiResponse exchange(WebClient.RequestHeadersSpec<?> spec) {
    return spec.exchangeToMono(response -> {
      log.debug("{} {}", response.statusCode(), response.headers().asHttpHeaders().toSingleValueMap());
      return RestApiResponse.fromClientResponse(response);
    }).block();
  }

}
