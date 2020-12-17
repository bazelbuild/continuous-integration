package build.bazel.dashboard.utils;

import java.time.Instant;

import static java.time.temporal.ChronoUnit.DAYS;

public enum Period {
  DAILY;

  public Instant truncate(Instant instant) {
    switch (this) {
      case DAILY:
        return instant.truncatedTo(DAYS);
      default:
        throw new UnsupportedOperationException();
    }
  }

  public Instant next(Instant instant) {
    switch (this) {
      case DAILY:
        return instant.plus(1, DAYS);
      default:
        throw new UnsupportedOperationException();
    }
  }
}
