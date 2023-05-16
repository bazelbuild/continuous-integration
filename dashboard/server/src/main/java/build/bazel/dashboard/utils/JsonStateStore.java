package build.bazel.dashboard.utils;

import java.time.Instant;
import java.util.List;
import javax.annotation.Nullable;
import lombok.Builder;
import lombok.Value;

public interface JsonStateStore {

  @Builder
  @Value
  class JsonState<T> {
    String key;
    Instant timestamp;
    @Nullable
    T data;
  }

  <T> void save(String key, @Nullable Instant lastTimestamp, T data);

  <T> JsonState<T> load(String key, Class<T> type);

  <T> List<JsonState<T>> findAllLike(String pattern, Class<T> type);

  void delete(String key, Instant lastTimestamp);
}
