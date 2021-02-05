package build.bazel.dashboard.config;

import build.bazel.dashboard.github.issuequery.GithubIssueQueryParser;
import build.bazel.dashboard.github.issuequery.GithubIssueQueryExecutor;
import build.bazel.dashboard.github.issuequery.GithubIssueQueryExecutorPg;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.web.reactive.function.client.ExchangeStrategies;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
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
  public GithubIssueQueryExecutor defaultGithubSearchExecutor(GithubIssueQueryParser queryParser, DatabaseClient databaseClient) {
    return new GithubIssueQueryExecutorPg(queryParser, databaseClient);
  }
}
