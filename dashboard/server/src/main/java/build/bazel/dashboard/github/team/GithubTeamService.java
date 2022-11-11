package build.bazel.dashboard.github.team;

import com.google.common.collect.ImmutableList;
import io.reactivex.rxjava3.core.Flowable;
import lombok.Builder;
import lombok.RequiredArgsConstructor;
import lombok.Value;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Service
@Slf4j
@RequiredArgsConstructor
public class GithubTeamService {
  private final GithubTeamRepo githubTeamRepo;

  @Builder
  @Value
  static class TeamsCacheKey {
    String owner;
    String repo;
  }

  public ImmutableList<GithubTeam> findAll(String owner, String repo) {
    return githubTeamRepo.list(owner, repo);
  }
}
