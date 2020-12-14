package build.bazel.dashboard.utils;

import io.reactivex.rxjava3.core.Single;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;

public class RxJavaFutures {
  private RxJavaFutures() {
  }

  public static <T> CompletableFuture<T> toCompletableFuture(Single<T> single, Executor executor) {
    return CompletableFuture.supplyAsync(single::blockingGet, executor);
  }
}
