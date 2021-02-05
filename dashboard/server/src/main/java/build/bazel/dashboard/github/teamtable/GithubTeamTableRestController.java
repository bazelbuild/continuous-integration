package build.bazel.dashboard.github.teamtable;

import io.reactivex.rxjava3.core.Single;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
public class GithubTeamTableRestController {
  private final GithubTeamTableService githubTeamTableService;

  @GetMapping("/github/{owner}/{repo}/team-tables/{tableId}")
  public Single<GithubTeamTable> findOne(
      @PathVariable("owner") String owner,
      @PathVariable("repo") String repo,
      @PathVariable("tableId") String tableId) {
    return githubTeamTableService.findOne(owner, repo, tableId);
  }
}
