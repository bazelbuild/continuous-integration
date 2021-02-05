package build.bazel.dashboard.github.teamtable;

import io.reactivex.rxjava3.core.Maybe;
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
    List<Header> headers;

    @Builder
    @Value
    public static class Header {
      String id;
      Instant createdAt;
      Instant updatedAt;
      String name;
      String query;
    }
  }

  Maybe<GithubTeamTableData> findOne(String owner, String repo, String tableId);
}
