resource "buildkite_pipeline" "rules-java-updates" {
  name           = "rules_java updates"
  repository     = "https://github.com/bazelbuild/rules_java.git"
  description    = "Update rules_java"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/java-tools-testing/pipelines/rules_java-updates.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
      ]
    }
  })
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
  branch_configuration       = null
  cluster_id                 = null
  color                      = null
  default_team_id            = null
  emoji                      = null
  pipeline_template_id       = null
  provider_settings = {
    # GitHub activities are disabled for this pipeline
    trigger_mode = "none"
  }
}

resource "buildkite_pipeline" "rules-java-release" {
  name           = "rules_java release"
  repository     = "https://github.com/bazelbuild/rules_java.git"
  description    = "Build and release rules_java"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/refs/heads/master/pipelines/rules_java-release.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
      ]
    }
  })
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
  branch_configuration       = null
  cluster_id                 = null
  color                      = null
  default_team_id            = null
  emoji                      = null
  pipeline_template_id       = null
  provider_settings = {
    # GitHub activities are disabled for this pipeline
    trigger_mode = "none"
  }
}

resource "buildkite_pipeline" "rules-platform-release" {
  name           = "rules_platform release"
  repository     = "https://github.com/bazelbuild/rules_platform.git"
  description    = "Build and release rules_platform"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/rules_platform-release.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
      ],
      label = ":pipeline:"
    }
  })
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
  branch_configuration       = null
  cluster_id                 = null
  color                      = null
  default_team_id            = null
  emoji                      = null
  pipeline_template_id       = null
  provider_settings = {
    # GitHub activities are disabled for this pipeline
    trigger_mode = "none"
  }
}

resource "buildkite_pipeline" "rules-platform-release-testing" {
  name           = "rules_platform release testing"
  repository     = "https://github.com/keertk/rules_platform.git"
  description    = "rules_platform release testing"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/rules_platform-release-testing/pipelines/rules_platform-release-testing.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
      ],
      label = ":pipeline:"
    }
  })
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
  branch_configuration       = null
  cluster_id                 = null
  color                      = null
  default_team_id            = null
  emoji                      = null
  pipeline_template_id       = null
  provider_settings = {
    # GitHub activities are disabled for this pipeline
    trigger_mode = "none"
  }
}
