package build.bazel.dashboard.github.repo;

import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Maybe;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class GithubRepoService {
  private final GithubRepoRepo githubRepoRepo;

  public Maybe<GithubRepo> findOne(String owner, String repo) {
    return githubRepoRepo.findOne(owner,repo);
  }

  public Flowable<GithubRepo> findAll() {
    return githubRepoRepo.findAll();
  }
}
