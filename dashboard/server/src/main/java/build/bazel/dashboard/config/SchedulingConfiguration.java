package build.bazel.dashboard.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.scheduling.annotation.EnableScheduling;

@Profile("scheduling")
@Configuration
@EnableScheduling
public class SchedulingConfiguration {
}
