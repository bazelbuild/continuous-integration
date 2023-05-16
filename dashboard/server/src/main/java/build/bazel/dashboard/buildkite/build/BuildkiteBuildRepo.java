package build.bazel.dashboard.buildkite.build;

import static build.bazel.dashboard.utils.PgJson.toPgJson;
import static java.util.Objects.requireNonNull;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.r2dbc.postgresql.codec.Json;
import io.r2dbc.spi.Readable;
import java.io.IOException;
import java.time.Instant;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class BuildkiteBuildRepo {

  private final DatabaseClient databaseClient;
  private final ObjectMapper objectMapper;

  public Optional<BuildkiteBuild> findOne(String org, String pipeline, int buildNumber) {
    return Optional.ofNullable(
        databaseClient
            .sql(
                "SELECT org, pipeline, build_number, timestamp, etag, data FROM buildkite_build_data "
                    + "WHERE org=:org AND pipeline=:pipeline AND build_number=:build_number")
            .bind("org", org)
            .bind("pipeline", pipeline)
            .bind("build_number", buildNumber)
            .map(this::toBuildkiteBuild)
            .one()
            .block());
  }

  public void save(BuildkiteBuild build) {
    databaseClient
        .sql(
            "INSERT INTO buildkite_build_data (org, pipeline, build_number, timestamp, etag, data)"
                + " VALUES (:org, :pipeline, :build_number, :timestamp, :etag, :data) ON"
                + " CONFLICT (org, pipeline, build_number) DO UPDATE SET etag = excluded.etag,"
                + " timestamp = excluded.timestamp, data = excluded.data")
        .bind("org", build.org())
        .bind("pipeline", build.pipeline())
        .bind("build_number", build.buildNumber())
        .bind("timestamp", build.timestamp())
        .bind("etag", build.etag())
        .bind("data", toPgJson(objectMapper, build.data()))
        .then()
        .block();
  }

  private BuildkiteBuild toBuildkiteBuild(Readable row) {
    try {
      return new BuildkiteBuild(
          requireNonNull(row.get("org", String.class)),
          requireNonNull(row.get("pipeline", String.class)),
          requireNonNull(row.get("build_number", Integer.class)),
          requireNonNull(row.get("timestamp", Instant.class)),
          requireNonNull(row.get("etag", String.class)),
          objectMapper.readTree((requireNonNull(row.get("data", Json.class))).asArray())
      );
    } catch (IOException e) {
      throw new IllegalStateException(e);
    }
  }
}
