package build.bazel.dashboard.github.api;

public record FetchPullRequestRequest(String owner, String repo, int issueNumber, String etag) {}
