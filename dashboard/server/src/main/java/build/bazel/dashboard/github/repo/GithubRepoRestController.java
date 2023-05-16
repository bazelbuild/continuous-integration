package build.bazel.dashboard.github.repo;

import static build.bazel.dashboard.utils.RxJavaVirtualThread.single;

import io.reactivex.rxjava3.core.Single;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
public class GithubRepoRestController {
  private final GithubRepoService githubRepoService;

  @GetMapping("/github/repos")
  public Single<List<GithubRepo>> findAll() {
    return single(githubRepoService::findAll);
  }
}
