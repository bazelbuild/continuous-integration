package build.bazel.dashboard.config;

import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Data
@NoArgsConstructor
@Configuration
@ConfigurationProperties(prefix = "dashboard")
public class DashboardConfig {
  @Data
  @NoArgsConstructor
  public static class GithubConfig {

    @Data
    @NoArgsConstructor
    public static class NotificationConfig {
      String fromEmail;
      String toNeedReviewEmail;
    }

    NotificationConfig notification;
  }

  String host;
  GithubConfig github;
}
