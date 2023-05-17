package build.bazel.dashboard.buildkite.build;

import static build.bazel.dashboard.utils.RxJavaVirtualThread.completable;
import static build.bazel.dashboard.utils.RxJavaVirtualThread.single;
import static com.google.common.base.Preconditions.checkNotNull;

import build.bazel.dashboard.utils.JsonStateStore;
import build.bazel.dashboard.utils.JsonStateStore.JsonState;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.common.hash.Hashing;
import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Single;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.Arrays;
import java.util.stream.Collectors;
import javax.annotation.Nullable;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.logging.log4j.util.Strings;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.RequestEntity;
import org.springframework.http.ResponseEntity;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@Slf4j
public class BuildkiteBuildSyncTask {

  private final BuildkiteBuildService buildkiteBuildService;
  private final JsonStateStore jsonStateStore;

  private final ObjectMapper objectMapper;

  @Value("${buildkite.webhookToken:}")
  private String buildkiteWebhookToken;

  @PostMapping("/webhook/buildkite")
  public Single<ResponseEntity<String>> webhook(RequestEntity<String> request) {
    return single(() -> {
      log.debug("{}", request);

      var signatureHeader = request.getHeaders().getFirst("X-Buildkite-Signature");
      if (signatureHeader == null) {
        return ResponseEntity.status(401).build();
      }

      var parts = Arrays.stream(signatureHeader.split(",")).map(part -> part.split("="))
          .filter(entry -> entry.length == 2 && !Strings.isBlank(entry[0]) && !Strings.isBlank(
              entry[1]))
          .collect(Collectors.toMap(entry -> entry[0], entry -> entry[1]));
      if (parts.get("timestamp") == null || parts.get("signature") == null) {
        return ResponseEntity.status(401).build();
      }

      var timestamp = Integer.parseInt(parts.get("timestamp"));
      var signature = parts.get("signature");

      var payload = request.getBody();
      var expected = Hashing.sha256()
          .hashString(String.format("%s.%s", timestamp, payload), StandardCharsets.UTF_8)
          .toString();
      if (!expected.equals(signature)) {
        return ResponseEntity.status(401).build();
      }

      var event = objectMapper.readTree(payload);
      buildkiteBuildService.onEvent(event);

      return ResponseEntity.ok().build();
    });
  }

  @PutMapping("/internal/buildkite/organizations/{org}/pipelines/{pipeline}/builds")
  public Completable saveNewSyncBuildState(
      @PathVariable("org") String org,
      @PathVariable("pipeline") String pipeline,
      @RequestParam(name = "start") Integer start,
      @RequestParam(name = "count") Integer count) {
    return completable(() -> saveNewSyncState(org, pipeline, start, start + count, null));
  }

  // We have a rate limit 100/min.
  @Scheduled(fixedDelay = 500)
  private void sync() {
    var states = jsonStateStore.findAllLike(SYNC_STATE_KEY_PREFIX + "%", SyncState.class);
    for (var state : states) {
      doSync(state);
      return;
    }
  }

  private void doSync(JsonState<SyncState> jsonState) {
    var data = jsonState.getData();
    checkNotNull(data);

    if (data.current >= data.end) {
      jsonStateStore.delete(jsonState.getKey(), jsonState.getTimestamp());
      return;
    }

    var unused = buildkiteBuildService.fetchAndSave(data.org(), data.pipeline(), data.current());
    jsonStateStore.save(
        jsonState.getKey(), jsonState.getTimestamp(),
        new SyncState(data.org(), data.pipeline(), data.start(),
            data.current() + 1, data.end()));
  }

  private void saveNewSyncState(
      String org, String pipeline, Integer start, Integer end, @Nullable Instant lastTimestamp) {
    jsonStateStore.save(
        buildSyncStateKey(org, pipeline),
        lastTimestamp,
        new SyncState(org, pipeline, start, start, end));
  }

  record SyncState(
      String org,
      String pipeline,
      int start,
      int current,
      int end
  ) {

  }

  private static final String SYNC_STATE_KEY_PREFIX = "sync-buildkite-builds";

  private String buildSyncStateKey(String org, String pipeline) {
    return String.format("%s/%s/%s", SYNC_STATE_KEY_PREFIX, org, pipeline);
  }
}
