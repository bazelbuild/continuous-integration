package build.bazel.dashboard.config;

import build.bazel.dashboard.github.issue.GithubSearchExecutor;
import build.bazel.dashboard.github.issue.PostgresqlGithubSearchExecutor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.web.reactive.function.client.ExchangeStrategies;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
@EnableScheduling
public class DefaultConfiguration {

  @Bean
  public WebClient defaultWebClient() {
    return WebClient.builder()
        .exchangeStrategies(
            ExchangeStrategies.builder()
                .codecs(
                    clientCodecConfigurer ->
                        clientCodecConfigurer
                            .defaultCodecs()
                            // Set in-memory buffer used to parse the body of http response to 10Mib
                            .maxInMemorySize(10 * 1024 * 1024))
                .build())
        .build();
  }

  @Bean
  public GithubSearchExecutor defaultGithubSearchExecutor(DatabaseClient databaseClient) {
    return new PostgresqlGithubSearchExecutor(databaseClient);
  }
}
