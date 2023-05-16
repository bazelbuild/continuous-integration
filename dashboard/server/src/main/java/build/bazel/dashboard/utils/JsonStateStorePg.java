package build.bazel.dashboard.utils;

import static build.bazel.dashboard.utils.PgJson.toPgJson;
import static java.util.Objects.requireNonNull;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.r2dbc.postgresql.codec.Json;
import java.io.IOException;
import java.time.Instant;
import java.util.Optional;
import javax.annotation.Nullable;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.OptimisticLockingFailureException;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Mono;

@Component
@Slf4j
@RequiredArgsConstructor
public class JsonStateStorePg implements JsonStateStore {

  private final DatabaseClient databaseClient;
  private final ObjectMapper objectMapper;

  @Override
  public <T> void save(String key, @Nullable Instant lastTimestamp, T data) {
    String sql =
        "INSERT INTO json_state (key, timestamp, data) VALUES (:key, CURRENT_TIMESTAMP,"
            + " :data) ON CONFLICT (key) DO UPDATE SET timestamp = CURRENT_TIMESTAMP,"
            + " data = excluded.data";

    if (lastTimestamp != null) {
      sql = sql + " WHERE json_state.timestamp = :last_timestamp";
    }

    DatabaseClient.GenericExecuteSpec spec = databaseClient.sql(sql).bind("key", key);

    spec = spec.bind("data", toPgJson(objectMapper, data));

    if (lastTimestamp != null) {
      spec = spec.bind("last_timestamp", lastTimestamp);
    }

    var count = Optional.ofNullable(spec.fetch().rowsUpdated().block()).orElse(0L);
    if (count != 1) {
      throw new OptimisticLockingFailureException("Failed to update: updated count is " + count);
    }
  }

  @Override
  public <T> JsonState<T> load(String key, Class<T> type) {
    Mono<JsonState<T>> query =
        databaseClient
            .sql("SELECT key, timestamp, data FROM json_state WHERE key = :key")
            .bind("key", key)
            .map(
                row -> {
                  try {
                    return JsonState.<T>builder()
                        .key(requireNonNull(row.get("key", String.class)))
                        .timestamp(requireNonNull(row.get("timestamp", Instant.class)))
                        .data(
                            objectMapper.readValue(
                                requireNonNull(row.get("data", Json.class)).asArray(), type))
                        .build();
                  } catch (IOException e) {
                    throw new RuntimeException(e);
                  }
                })
            .one()
            .defaultIfEmpty(
                JsonState.<T>builder().key(key).timestamp(Instant.EPOCH).data(null).build());
    return query.block();
  }

  @Override
  public void delete(String key, Instant lastTimestamp) {
    var count =
        Optional.ofNullable(
                databaseClient
                    .sql("DELETE FROM json_state WHERE key = :key AND timestamp = :last_timestamp")
                    .bind("key", key)
                    .bind("last_timestamp", lastTimestamp)
                    .fetch()
                    .rowsUpdated()
                    .block())
            .orElse(0L);
    if (count != 1) {
      throw new OptimisticLockingFailureException("Failed to delete: count is " + count);
    }
  }
}
