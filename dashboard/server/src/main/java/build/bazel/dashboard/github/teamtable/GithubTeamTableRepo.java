package build.bazel.dashboard.github.teamtable;

import io.reactivex.rxjava3.core.Maybe;
import java.util.Optional;
import lombok.Builder;
import lombok.Value;

import java.time.Instant;
import java.util.List;

public interface GithubTeamTableRepo {
  @Builder
  @Value
  class GithubTeamTableData {
    String owner;
    String repo;
    String id;
    Instant createdAt;
    Instant updatedAt;
    String name;
    String noneTeamOwner;
    List<Header> headers;

    @Builder
    @Value
    public static class Header {
      String id;
      Instant createdAt;
      Instant updatedAt;
      Integer seq;
      String name;
      String query;
    }
  }

  Optional<GithubTeamTableData> findOne(String owner, String repo, String tableId);
}
