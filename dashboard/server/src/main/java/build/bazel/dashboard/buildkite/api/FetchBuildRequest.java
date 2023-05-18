package build.bazel.dashboard.buildkite.api;

public record FetchBuildRequest(
    String org,
    String pipeline,
    int buildNumber,
    String etag
) {
  public static FetchBuildRequest create(String org, String pipeline, int buildNumber, String etag) {
    return new FetchBuildRequest(org, pipeline, buildNumber, etag);
  }
}
