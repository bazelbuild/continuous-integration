package build.bazel.dashboard.github.repo;

import io.reactivex.rxjava3.core.Flowable;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class GithubRepoService {
  private final GithubRepoRepo githubRepoRepo;

  public Flowable<GithubRepo> findAll() {
    return githubRepoRepo
        .findAll()
        .map(data -> GithubRepo.builder().owner(data.getOwner()).repo(data.getRepo()).build());
  }
}
