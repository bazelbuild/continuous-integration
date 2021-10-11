package build.bazel.dashboard.github.repo;

import io.reactivex.rxjava3.core.Flowable;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
public class GithubRepoRestController {
  private final GithubRepoService githubRepoService;

  @GetMapping("/github/repos")
  public Flowable<GithubRepo> findAll() {
    return githubRepoService.findAll();
  }
}
