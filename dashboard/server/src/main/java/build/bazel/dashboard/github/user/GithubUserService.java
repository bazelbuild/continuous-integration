package build.bazel.dashboard.github.user;

import io.reactivex.rxjava3.core.Flowable;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class GithubUserService {
  private final GithubUserRepo githubUserRepo;

  public Flowable<GithubUser> findAll() {
    return githubUserRepo.findAll();
  }
}
