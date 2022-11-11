package build.bazel.dashboard.utils;

import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Maybe;
import io.reactivex.rxjava3.core.Single;
import io.reactivex.rxjava3.functions.Action;
import java.util.Optional;
import java.util.concurrent.Callable;

public class RxJavaVirtualThread {
  private RxJavaVirtualThread() {}

  public static <T> Single<T> single(Callable<T> task) {
    return Single.create(
        emitter -> {
          var thread =
              Thread.startVirtualThread(
                  () -> {
                    try {
                      var result = task.call();
                      emitter.onSuccess(result);
                    } catch (Throwable e) {
                      emitter.onError(e);
                    }
                  });
          emitter.setCancellable(thread::interrupt);
        });
  }

  public static <T> Maybe<T> maybe(Callable<Optional<T>> task) {
    return Maybe.create(
        emitter -> {
          var thread =
              Thread.startVirtualThread(
                  () -> {
                    try {
                      var result = task.call();
                      if (result.isPresent()) {
                        emitter.onSuccess(result.get());
                      } else {
                        emitter.onComplete();
                      }
                    } catch (Throwable e) {
                      emitter.onError(e);
                    }
                  });
          emitter.setCancellable(thread::interrupt);
        });
  }

  public static Completable completable(Action task) {
    return Completable.create(
        emitter -> {
          var thread =
              Thread.startVirtualThread(
                  () -> {
                    try {
                      task.run();
                      emitter.onComplete();
                    } catch (Throwable e) {
                      emitter.onError(e);
                    }
                  });
          emitter.setCancellable(thread::interrupt);
        });
  }
}
