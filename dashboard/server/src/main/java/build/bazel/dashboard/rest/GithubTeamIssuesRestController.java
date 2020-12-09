package build.bazel.dashboard.rest;

import build.bazel.dashboard.github.issue.GithubIssuesApi;
import build.bazel.dashboard.github.issue.ListRepositoryIssuesRequest;
import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

@RestController
public class GithubTeamIssuesRestController {
    private final GithubIssuesApi githubIssuesApi;

    @Autowired
    public GithubTeamIssuesRestController(GithubIssuesApi githubIssuesApi) {
        this.githubIssuesApi = githubIssuesApi;
    }

    @GetMapping("/github/teams/issues")
    public Mono<JsonNode> listGithubTeamIssues() {
        ListRepositoryIssuesRequest request = ListRepositoryIssuesRequest.builder()
                .owner("bazelbuild")
                .repo("bazel")
                .perPage(100)
                .page(0)
                .build();
        return githubIssuesApi.listRepositoryIssues(request);
    }
}
