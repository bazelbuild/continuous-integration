package build.bazel.dashboard.utils;

import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Single;
import lombok.Builder;
import lombok.Value;

import javax.annotation.Nullable;
import java.time.Instant;

public interface JsonStateStore {

  @Builder
  @Value
  class JsonState<T> {
    String key;
    Instant timestamp;
    @Nullable
    T data;
  }

  <T> Completable save(String key, @Nullable Instant lastTimestamp, T data);

  <T> Single<JsonState<T>> load(String key, Class<T> type);

  Completable delete(String key, Instant lastTimestamp);
}
