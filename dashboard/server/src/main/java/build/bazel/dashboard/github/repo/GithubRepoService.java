package build.bazel.dashboard.github.repo;

import com.google.common.collect.ImmutableList;
import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Maybe;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class GithubRepoService {
  private final GithubRepoRepo githubRepoRepo;

  public Optional<GithubRepo> findOne(String owner, String repo) {
    return githubRepoRepo.findOne(owner,repo);
  }

  public ImmutableList<GithubRepo> findAll() {
    return githubRepoRepo.findAll();
  }
}
