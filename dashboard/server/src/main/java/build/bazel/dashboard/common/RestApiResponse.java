package build.bazel.dashboard.common;

import static build.bazel.dashboard.utils.HttpHeadersUtils.getAsIntOrZero;
import static build.bazel.dashboard.utils.HttpHeadersUtils.getOrEmpty;

import com.fasterxml.jackson.databind.JsonNode;
import lombok.Builder;
import lombok.Value;
import org.springframework.http.HttpStatusCode;
import org.springframework.web.reactive.function.client.ClientResponse;
import reactor.core.publisher.Mono;

@Builder
@Value
public class RestApiResponse {
  HttpStatusCode status;
  String etag;
  RateLimit rateLimit;
  JsonNode body;

  @Builder
  @Value
  public static class RateLimit {
    int limit;
    int remaining;
    int used;
    int reset;

    public static RateLimit fromHeaders(ClientResponse.Headers headers) {
      RateLimitBuilder builder = RateLimit.builder();
      builder.limit(getAsIntOrZero(headers, "X-RateLimit-Limit"));
      builder.remaining(getAsIntOrZero(headers, "X-RateLimit-Remaining"));
      builder.used(getAsIntOrZero(headers, "X-RateLimit-Used"));
      builder.reset(getAsIntOrZero(headers, "X-RateLimit-Reset"));
      return builder.build();
    }
  }

  public static Mono<RestApiResponse> fromClientResponse(ClientResponse clientResponse) {
    var status = clientResponse.statusCode();
    ClientResponse.Headers headers = clientResponse.headers();
    var builder =
        RestApiResponse.builder()
            .status(status)
            .etag(getOrEmpty(headers, "ETag"))
            .rateLimit(RateLimit.fromHeaders(headers));

    if (status.is2xxSuccessful()) {
      return clientResponse.bodyToMono(JsonNode.class).map(body -> builder.body(body).build());
    } else {
      return Mono.just(builder.build());
    }
  }
}
