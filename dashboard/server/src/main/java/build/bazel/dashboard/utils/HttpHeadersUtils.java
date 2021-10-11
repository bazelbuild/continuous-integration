package build.bazel.dashboard.utils;

import org.springframework.web.reactive.function.client.ClientResponse;

public final class HttpHeadersUtils {
  private HttpHeadersUtils() {
  }

  public static int getAsIntOrZero(ClientResponse.Headers headers, String headerName) {
    try {
      return Integer.parseInt(headers.header(headerName).stream().findFirst().orElse("0"));
    } catch (NumberFormatException ignored) {
      return 0;
    }
  }

  public static String getOrEmpty(ClientResponse.Headers headers, String headerName) {
    return headers.header(headerName).stream().findFirst().orElse("");
  }
}
