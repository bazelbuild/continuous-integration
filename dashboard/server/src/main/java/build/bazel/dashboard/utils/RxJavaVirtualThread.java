package build.bazel.dashboard.utils;

import io.reactivex.rxjava3.core.Single;
import java.util.concurrent.Callable;

public class RxJavaVirtualThread {
  private RxJavaVirtualThread() {}

  public static <T> Single<T> single(Callable<T> task) {
    return Single.create(emitter -> {
      var thread = Thread.startVirtualThread(() -> {
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
}
