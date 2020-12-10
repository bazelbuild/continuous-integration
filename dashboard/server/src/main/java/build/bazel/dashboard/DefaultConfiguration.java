package build.bazel.dashboard;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.web.reactive.function.client.ExchangeStrategies;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
@EnableScheduling
public class DefaultConfiguration {

  @Bean
  public WebClient webClient() {
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
}
