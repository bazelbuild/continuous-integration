package build.bazel.dashboard.github;

import org.springframework.web.util.UriComponentsBuilder;

import java.net.URLEncoder;

import static java.nio.charset.StandardCharsets.UTF_8;

public class GithubUtils {
  public static String buildIssueQueryUrl(String owner, String repo, String query) {
    return UriComponentsBuilder.newInstance()
        .scheme("https")
        .host("github.com")
        .pathSegment(owner, repo, "issues")
        .queryParam("q", URLEncoder.encode(query, UTF_8))
        .build()
        .toString();
  }
}
