package build.bazel.dashboard.buildkite.api;

import static com.google.common.base.Preconditions.checkNotNull;

import build.bazel.dashboard.common.RestApiClient;
import build.bazel.dashboard.common.RestApiResponse;
import com.google.common.base.Strings;
import java.net.URI;
import java.util.Optional;
import java.util.function.Function;
import javax.annotation.Nullable;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClient.RequestHeadersSpec;
import org.springframework.web.util.UriBuilder;

@Component
@Slf4j
public class BuildkiteRestApiClient extends RestApiClient {
  private final String accessToken;

  public BuildkiteRestApiClient(WebClient webClient, @Value("${buildkite.accessToken:}") String accessToken) {
    super("https", "api.buildkite.com", webClient);
    this.accessToken = accessToken;
  }

  public RestApiResponse listBuilds(ListBuildsRequest request) {
    log.debug("{}", request);

    checkNotNull(request.org());
    checkNotNull(request.pipeline());

    var spec =
        get(
            uriBuilder ->
                uriBuilder
                    .pathSegment("v2", "organizations", request.org(), "pipelines", request.pipeline(), "builds")
                    .queryParamIfPresent("branch", Optional.ofNullable(request.branch()))
                    .queryParamIfPresent("page", Optional.ofNullable(request.page()))
                    .queryParamIfPresent("per_page", Optional.ofNullable(request.perPage()))
                    .build(), request.etag());

    return exchange(spec);
  }

  public RestApiResponse fetchBuild(FetchBuildRequest request) {
    log.debug("{}", request);

    checkNotNull(request.org());
    checkNotNull(request.pipeline());

    var spec =
        get(
            uriBuilder ->
                uriBuilder
                    .pathSegment("v2", "organizations", request.org(), "pipelines", request.pipeline(), "builds", String.valueOf(request.buildNumber()))
                    .build(), request.etag());

    return exchange(spec);
  }

  @Override
  protected RequestHeadersSpec<?> get(Function<UriBuilder, URI> uriFunction, @Nullable String etag) {
    var spec = super.get(uriFunction, etag);
    if (!Strings.isNullOrEmpty(accessToken)) {
      spec.header("Authorization", "Bearer " + accessToken);
    }
    return spec;
  }
}
