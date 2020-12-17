package build.bazel.dashboard.github;

import lombok.Builder;
import lombok.Value;

import java.time.Instant;

@Builder
@Value
public class GithubTeamIssue {
    GithubIssueTeam team;
    Stats openIssues;
    Stats openP0Issues;
    Stats openP1Issues;
    Stats openP2Issues;
    Stats openP3Issues;
    Stats openP4Issues;
    Stats openNoTypeIssues;
    Stats openNoPriorityIssues;
    Stats openUntriagedIssues;
    Instant updatedAt;

    @Builder
    @Value
    public static class Stats {
        String url;
        Integer count;
    }
}
