package build.bazel.dashboard.github.issue;

import lombok.Builder;
import lombok.Value;

import java.time.Instant;

@Builder
@Value
public class GithubTeamIssue {
    Team team;
    IssueStats openIssues;
    IssueStats openP0Issues;
    IssueStats openP1Issues;
    IssueStats openP2Issues;
    IssueStats openP3Issues;
    IssueStats openP4Issues;
    IssueStats openNoTypeIssues;
    IssueStats openNoPriorityIssues;
    IssueStats openUntriagedIssues;
    Instant updatedAt;

    @Builder
    @Value
    public static class Team {
      String name;
      String owner;
      String label;
    }

    @Builder
    @Value
    public static class IssueStats {
        String url;
        Integer count;
    }
}
