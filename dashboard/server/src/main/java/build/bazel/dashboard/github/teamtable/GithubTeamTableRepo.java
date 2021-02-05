package build.bazel.dashboard.github.teamtable;

import io.reactivex.rxjava3.core.Maybe;
import lombok.Builder;
import lombok.Value;

import java.util.List;

public interface GithubTeamTableRepo {
  @Builder
  @Value
  class GithubTeamTableData {
    String owner;
    String repo;
    String id;
    String name;
    List<Header> headers;

    @Builder
    @Value
    public static class Header {
      String id;
      String name;
      String query;
    }
  }

  Maybe<GithubTeamTableData> findOne(String owner, String repo, String tableId);
}
