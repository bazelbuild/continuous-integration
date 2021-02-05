package build.bazel.dashboard.github.teamtable;

import build.bazel.dashboard.github.teamtable.GithubTeamTableRepo.GithubTeamTableData.Header;
import com.google.common.collect.ImmutableList;
import io.reactivex.rxjava3.core.Maybe;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public class GithubTeamTableRepoPg implements GithubTeamTableRepo {
  private final List<GithubTeamTableData> data =
      ImmutableList.of(
          GithubTeamTableData.builder()
              .owner("bazelbuild")
              .repo("bazel")
              .id("open-issues")
              .name("Open Issues by Team")
              .headers(
                  ImmutableList.of(
                      Header.builder().id("total").name("Total").query("is:issue is:open").build(),
                      Header.builder()
                          .id("p0")
                          .name("P0")
                          .query("is:issue is:open label:P0")
                          .build(),
                      Header.builder()
                          .id("p1")
                          .name("P1")
                          .query("is:issue is:open label:P1")
                          .build(),
                      Header.builder()
                          .id("p2")
                          .name("P2")
                          .query("is:issue is:open label:P2")
                          .build(),
                      Header.builder()
                          .id("p3")
                          .name("P3")
                          .query("is:issue is:open label:P3")
                          .build(),
                      Header.builder()
                          .id("p4")
                          .name("P4")
                          .query("is:issue is:open label:P4")
                          .build(),
                      Header.builder()
                          .id("no-type")
                          .name("No Type")
                          .query(
                              "is:issue is:open "
                                  + "-label:\"type: process\" "
                                  + "-label:\"type: support / not a bug (process)\" "
                                  + "-label:\"type: documentation (cleanup)\" "
                                  + "-label:\"type: bug\" "
                                  + "-label:\"type: feature request\" ")
                          .build(),
                      Header.builder()
                          .id("no-priority")
                          .name("No Priority")
                          .query(
                              "is:issue is:open "
                                  + "-label:P0 "
                                  + "-label:P1 "
                                  + "-label:P2 "
                                  + "-label:P3 "
                                  + "-label:P4 ")
                          .build(),
                      Header.builder()
                          .id("untriaged")
                          .name("Untriaged")
                          .query("is:issue is:open label:untriaged")
                          .build(),
                      Header.builder().id("pr").name("PR").query("is:pr is:open").build()))
              .build());

  @Override
  public Maybe<GithubTeamTableData> findOne(String owner, String repo, String tableId) {
    return Maybe.fromOptional(
        data.stream()
            .filter(
                it ->
                    it.getOwner().equals(owner)
                        && it.getRepo().equals(repo)
                        && it.getId().equals(tableId))
            .findFirst());
  }
}
