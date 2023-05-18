package build.bazel.dashboard.buildkite.api;

import javax.annotation.Nullable;

public record ListBuildsRequest(
    String org,
    String pipeline,
    @Nullable
    String branch,
    @Nullable
    Integer perPage,
    @Nullable
    Integer page,
    @Nullable
    String etag
) {

}
