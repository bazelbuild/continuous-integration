package build.bazel.dashboard.utils;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.r2dbc.postgresql.codec.Json;
import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Single;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.OptimisticLockingFailureException;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Component;
import reactor.adapter.rxjava.RxJava3Adapter;
import reactor.core.publisher.Mono;

import javax.annotation.Nullable;
import java.io.IOException;
import java.time.Instant;

import static java.util.Objects.requireNonNull;

@Component
@Slf4j
@RequiredArgsConstructor
public class JsonStateStorePg implements JsonStateStore {

  private final DatabaseClient databaseClient;
  private final ObjectMapper objectMapper;

  @Override
  public <T> Completable save(String key, @Nullable Instant lastTimestamp, T data) {
    String sql =
        "INSERT INTO json_state (key, timestamp, data) VALUES (:key, CURRENT_TIMESTAMP,"
            + " :data) ON CONFLICT (key) DO UPDATE SET timestamp = CURRENT_TIMESTAMP,"
            + " data = excluded.data";

    if (lastTimestamp != null) {
      sql = sql + " WHERE json_state.timestamp = :last_timestamp";
    }

    DatabaseClient.GenericExecuteSpec spec = databaseClient.sql(sql).bind("key", key);

    try {
      spec = spec.bind("data", Json.of(objectMapper.writeValueAsBytes(data)));
    } catch (JsonProcessingException e) {
      return Completable.error(e);
    }

    if (lastTimestamp != null) {
      spec = spec.bind("last_timestamp", lastTimestamp);
    }

    Mono<Integer> execution = spec.fetch().rowsUpdated().defaultIfEmpty(0);
    return RxJava3Adapter.monoToSingle(execution)
        .flatMapCompletable(
            count -> {
              if (count != 1) {
                return Completable.error(
                    new OptimisticLockingFailureException(
                        "Failed to update: updated count is " + count));
              }
              return Completable.complete();
            });
  }

  @Override
  public <T> Single<JsonState<T>> load(String key, Class<T> type) {
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
    return RxJava3Adapter.monoToSingle(query);
  }

  @Override
  public Completable delete(String key, Instant lastTimestamp) {
    Mono<Integer> query =
        databaseClient
            .sql("DELETE FROM json_state WHERE key = :key AND timestamp = :last_timestamp")
            .bind("key", key)
            .bind("last_timestamp", lastTimestamp)
            .fetch()
            .rowsUpdated()
            .defaultIfEmpty(0);
    return RxJava3Adapter.monoToSingle(query)
        .flatMapCompletable(
            count -> {
              if (count != 1) {
                return Completable.error(
                    new OptimisticLockingFailureException("Failed to delete: count is " + count));
              }
              return Completable.complete();
            });
  }
}
