terraform {
  backend "gcs" {
    bucket = "bazel-buildkite-tf-state"
    prefix = "bazel-testing"
  }

  required_providers {
    buildkite = {
      source  = "buildkite/buildkite"
      version = "~> 1.0"
    }
  }
}

provider "buildkite" {
  # can also be set from env: BUILDKITE_API_TOKEN
  # api_token    = ""
  organization = "bazel-testing"
}

# 1. upb
resource "buildkite_pipeline" "upb" {
  name       = "upb"
  repository = "https://github.com/protocolbuffers/upb.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 2. bcr-presubmit
resource "buildkite_pipeline" "bcr-presubmit" {
  name        = "BCR Presubmit"
  repository  = "https://github.com/meteorcloudy/bazel-central-registry.git"
  description = "The presubmit for adding new Bazel module into the Bazel Central Registry"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {
      ENABLE_BAZELISK_MIGRATE = "1"
      # USE_BAZEL_VERSION: "7.4.0rc3"
      # INCOMPATIBLE_FLAGS: "--incompatible_enable_deprecated_label_apis,--incompatible_disable_native_repo_rules"
      # USE_BAZELISK_MIGRATE: "1"
      # CI_RESOURCE_PERCENTAGE: 100
      # MODULE_SELECTIONS: "rules_cc@latest,rules_java@latest,protobuf@latest"
      # SMOKE_TEST_PERCENTAGE: 100
    }
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/pcloudy-bcr-test/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/pcloudy-bcr-test/buildkite/bazel-central-registry/bcr_presubmit.py?$(date +%s)\" -o bcr_presubmit.py",
        "python3 bcr_presubmit.py bcr_presubmit"
      ]
    }
  })
  default_branch             = "main"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []

  provider_settings = {
    trigger_mode                             = "code"
    build_pull_requests                      = true
    build_pull_request_forks                 = true
    prefix_pull_request_fork_branch_names    = true
    publish_commit_status_per_step           = true
    publish_blocked_as_pending               = true
    filter_enabled                           = true
    pull_request_branch_filter_configuration = "*@*"
    filter_condition                         = "build.pull_request.labels includes \"bcr-presubmit\""
  }
}

# 3. protobuf
resource "buildkite_pipeline" "protobuf" {
  name       = "Protobuf"
  repository = "https://github.com/protocolbuffers/protobuf.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/protobuf-postsubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []

  provider_settings = {
    trigger_mode                                  = "code"
    build_pull_requests                           = true
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names         = true
    build_branches                                = true
  }
}

# 4. intellij-plugin
resource "buildkite_pipeline" "intellij-plugin" {
  name       = "IntelliJ plugin"
  repository = "https://github.com/bazelbuild/intellij.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --file_config=.bazelci/aspect.yml | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 5. google-bazel-presubmit
resource "buildkite_pipeline" "google-bazel-presubmit" {
  name       = "Google Bazel Presubmit"
  repository = "https://bazel.googlesource.com/bazel.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 6. tulsi-bazel-darwin
resource "buildkite_pipeline" "tulsi-bazel-darwin" {
  name       = "Tulsi :bazel: :darwin:"
  repository = "https://github.com/bazelbuild/tulsi.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 7. apple-support-darwin
resource "buildkite_pipeline" "apple-support-darwin" {
  name       = "apple_support :darwin:"
  repository = "https://github.com/bazelbuild/apple_support.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 8. rules-apple-darwin
resource "buildkite_pipeline" "rules-apple-darwin" {
  name       = "rules_apple :darwin:"
  repository = "https://github.com/bazelbuild/rules_apple.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 9. android-testing
resource "buildkite_pipeline" "android-testing" {
  name       = "Android Testing"
  repository = "https://github.com/googlesamples/android-testing.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --file_config=bazelci/buildkite-pipeline.yml | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "main"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 10. rules-swift-swift
resource "buildkite_pipeline" "rules-swift-swift" {
  name       = "rules_swift :swift:"
  repository = "https://github.com/bazelbuild/rules_swift.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 11. rules-scala-scala
resource "buildkite_pipeline" "rules-scala-scala" {
  name       = "rules_scala :scala:"
  repository = "https://github.com/bazelbuild/rules_scala.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 12. rules-groovy
resource "buildkite_pipeline" "rules-groovy" {
  name       = "rules_groovy"
  repository = "https://github.com/bazelbuild/rules_groovy.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 13. rules-rust-rustlang
resource "buildkite_pipeline" "rules-rust-rustlang" {
  name       = "rules_rust :rustlang:"
  repository = "https://github.com/bazelbuild/rules_rust.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "main"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 14. rules-kotlin-kotlin
resource "buildkite_pipeline" "rules-kotlin-kotlin" {
  name       = "rules_kotlin :kotlin:"
  repository = "https://github.com/bazelbuild/rules_kotlin.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 15. rules-go-golang
resource "buildkite_pipeline" "rules-go-golang" {
  name       = "rules_go :golang:"
  repository = "https://github.com/bazel-contrib/rules_go.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 16. rules-nodejs-nodejs
resource "buildkite_pipeline" "rules-nodejs-nodejs" {
  name       = "rules_nodejs :nodejs:"
  repository = "https://github.com/bazelbuild/rules_nodejs.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --monitor_flaky_tests=true | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "main"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 17. publish-bazel-binaries
resource "buildkite_pipeline" "publish-bazel-binaries" {
  name        = "Publish Bazel binaries"
  repository  = "https://github.com/bazelbuild/bazel.git"
  description = "Publish Bazel binaries to GCS (http://storage.googleapis.com/bazel-testing-builds/metadata/latest.json)"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/pipelines/publish-bazel-binaries.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  branch_configuration       = "master"
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 18. bazelisk-plus-incompatible-flags
resource "buildkite_pipeline" "bazelisk-plus-incompatible-flags" {
  name        = "Bazelisk + Incompatible flags"
  repository  = "https://github.com/bazelbuild/bazel.git"
  description = "Use bazelisk --migrate to test incompatible flags with downstream projects@last_green_commit"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {
      USE_BAZELISK_MIGRATE = "true"
    }
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py bazel_downstream_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 19. bazel-at-head-plus-disabled
resource "buildkite_pipeline" "bazel-at-head-plus-disabled" {
  name        = "Bazel@HEAD + Disabled"
  repository  = "https://github.com/bazelbuild/bazel.git"
  description = "Test disabled downstream projects to see if they are already fixed."
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py bazel_downstream_pipeline --file_config=.bazelci/build_bazel_binaries.yml --test_disabled_projects | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 20. bazel-at-head-plus-downstream
resource "buildkite_pipeline" "bazel-at-head-plus-downstream" {
  name        = "Bazel@HEAD + Downstream"
  repository  = "https://github.com/bazelbuild/bazel.git"
  description = "Test Bazel@HEAD + downstream projects@last_green_commit"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {
      BAZELCI_DOWNSTREAM_PIPELINE = "true"
    }
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py bazel_downstream_pipeline --file_config=.bazelci/build_bazel_binaries.yml | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 21. bazelisk
resource "buildkite_pipeline" "bazelisk" {
  name       = "Bazelisk"
  repository = "https://github.com/bazelbuild/bazelisk.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --file_config=.bazelci/config.yml | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  branch_configuration       = "master"
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 22. bazel-bazel-github-presubmit
resource "buildkite_pipeline" "bazel-bazel-github-presubmit" {
  name       = "Bazel :bazel: Github Presubmit"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  branch_configuration       = "!*"
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 23. bazel-bazel
resource "buildkite_pipeline" "bazel-bazel" {
  name       = "Bazel :bazel:"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {
      LC_ALL = "en_US.UTF-8"
    }
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/collect_metrics.py?$(date +%s)\" -o collect_metrics.py",
        "python3.6 bazelci.py project_pipeline --file_config=.bazelci/postsubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  branch_configuration       = "master release-*"
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 24. rules-docker-docker
resource "buildkite_pipeline" "rules-docker-docker" {
  name       = "rules_docker :docker:"
  repository = "https://github.com/bazelbuild/rules_docker.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 25. flogger
resource "buildkite_pipeline" "flogger" {
  name       = "Flogger"
  repository = "https://github.com/google/flogger.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/flogger.yml?$(date +%s) | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 26. test-macos
# pipeline.yml is not used here as it doesn't apply to macos
resource "buildkite_pipeline" "test-macos" {
  name                       = "Test macOS"
  repository                 = "https://github.com/bazelbuild/continuous-integration.git"
  steps                      = "# This default command changes the pipeline of a running build by uploading a configuration file.\n# https://buildkite.com/docs/agent/v3/cli-pipeline\n# For information on different step types, check out the sidebar to the right.\n\nsteps:\n- agents: {queue: macos_arm64}\n  command: ['echo \"hello\" | sha1sum']\n  label: ':macOS: Test'\n- agents: {queue: macos_arm64}\n  command: ['echo \"hello\" | sha1sum']\n  label: ':macOS: Test'\n- agents: {queue: macos_arm64}\n  command: ['echo \"hello\" | sha1sum']\n  label: ':macOS: Test'\n- agents: {queue: macos_arm64}\n  command: ['echo \"hello\" | sha1sum']\n  label: ':macOS: Test'\n- agents: {queue: macos_arm64}\n  command: ['echo \"hello\" | sha1sum']\n  label: ':macOS: Test'\n- agents: {queue: macos_arm64}\n  command: ['echo \"hello\" | sha1sum']\n  label: ':macOS: Test'\n- agents: {queue: macos_arm64}\n  command: ['echo \"hello\" | sha1sum']\n  label: ':macOS: Test'"
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 27. bazel-auto-sheriff
resource "buildkite_pipeline" "bazel-auto-sheriff" {
  name        = "Bazel Auto Sheriff"
  repository  = "https://github.com/bazelbuild/continuous-integration.git"
  description = "Testing the auto sheriff pipeline"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      label = ":male-police-officer: :female-police-officer: :police_car:"
      commands = [
        "cd buildkite",
        "python3.6 bazel_auto_sheriff.py"
      ]
    }
  })
  default_branch             = "testing"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 28. fwe-test
resource "buildkite_pipeline" "fwe-test" {
  name       = "fwe-test"
  repository = "https://github.com/fweikert/bazel"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/fweikert/continuous-integration/refs/heads/co2/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "# Optional: Add --monitor_flaky_tests=true to disable receiving remote cache",
        "python3.6 bazelci.py --script https://raw.githubusercontent.com/fweikert/continuous-integration/refs/heads/co2/buildkite/bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/bazel-postsubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 29. bcr-compatibility-test
resource "buildkite_pipeline" "bcr-compatibility-test" {
  name        = "BCR Compatibility Test"
  repository  = "https://github.com/meteorcloudy/bazel-central-registry.git"
  description = "Test any given Bazel version with any given BCR modules and optionally with incompatible flags."
  steps = templatefile("pipeline.yml.tpl", {
    envs = {
      USE_BAZEL_VERSION      = "8.0.0rc2"
      CI_RESOURCE_PERCENTAGE = 100
      MODULE_SELECTIONS      = "rules_android@latest,rules_cc@latest,rules_kotlin@latest"
      SELECT_TOP_BCR_MODULES = 5
    }
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/select_top_modules/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/select_top_modules/buildkite/bazel-central-registry/bcr_presubmit.py?$(date +%s)\" -o bcr_presubmit.py",
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/select_top_modules/buildkite/bazel-central-registry/bcr_compatibility.py?$(date +%s)\" -o bcr_compatibility.py",
        "python3 bcr_compatibility.py"
      ]
    }
  })
  default_branch             = "fix_module_analyzer"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 30. bazel-bazel-arm64
resource "buildkite_pipeline" "bazel-bazel-arm64" {
  name       = ":bazel: Bazel (arm64)"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/bazel-linux-arm64.yml?$(date +%s) | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 31. aswb-plugin
resource "buildkite_pipeline" "aswb-plugin" {
  name       = "ASwB plugin"
  repository = "https://github.com/mai93/aswb-plugin.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --file_config=.bazelci/android-studio.yml | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "main"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

# 32. test-bazel-for-ci-metrics
resource "buildkite_pipeline" "test-bazel-for-ci-metrics" {
  name        = "Test Bazel For CI-Metrics"
  repository  = "https://github.com/bazelbuild/bazel.git"
  description = "a fast, scalable, multi-language and extensible build system"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {
      LC_ALL = "en_US.UTF-8"
    }
    steps = {
      queue = "metrics-test"
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/collect_metrics.py?$(date +%s)\" -o collect_metrics.py",
        "python3.6 -m pip install --upgrade pip setuptools wheel",
        "python3.6 -m pip install google-cloud-bigquery requests",
        "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/bazel/refs/heads/test-metrics/.bazelci/postsubmit.yml | tee /dev/tty | buildkite-agent pipeline upload",
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}