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
    trigger_mode                                  = "code"
    build_branches                                = false
    build_pull_requests                           = true
    build_tags                                    = false
    build_pull_request_forks                      = true
    build_pull_request_ready_for_review           = false
    build_pull_request_labels_changed             = false
    build_pull_request_base_branch_changed        = false
    prefix_pull_request_fork_branch_names         = true
    filter_enabled                                = true
    filter_condition                              = "build.pull_request.labels includes \"bcr-presubmit\""
    pull_request_branch_filter_enabled            = false
    pull_request_branch_filter_configuration      = "*@*"
    publish_commit_status                         = false
    publish_commit_status_per_step                = true
    separate_pull_request_statuses                = false
    publish_blocked_as_pending                    = true
    cancel_deleted_branch_builds                  = false
    skip_builds_for_existing_commits              = false
    skip_pull_request_builds_for_existing_commits = false
    ignore_default_branch_pull_requests           = false
    build_merge_group_checks_requested            = false
    cancel_when_merge_group_destroyed             = false
    use_merge_group_base_commit_for_git_diff_base = false
  }
}

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
  provider_settings = {
    # GitHub activities are disabled for this pipeline
    trigger_mode = "none"
  }
}

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
  provider_settings = {
    # GitHub activities are disabled for this pipeline
    trigger_mode = "none"
  }
}

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
  provider_settings = {
    # GitHub activities are disabled for this pipeline
    trigger_mode = "none"
  }
}

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
  provider_settings = {
    # GitHub activities are disabled for this pipeline
    trigger_mode = "none"
  }
}

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
  provider_settings = {
    # GitHub activities are disabled for this pipeline
    trigger_mode = "none"
  }
}

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
  provider_settings = {
    # GitHub activities are disabled for this pipeline
    trigger_mode = "none"
  }
}

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
  provider_settings = {
    # GitHub activities are disabled for this pipeline
    trigger_mode = "none"
  }
}

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
  provider_settings = {
    trigger_mode                                  = "code"
    build_branches                                = true
    build_pull_requests                           = true
    build_tags                                    = false
    build_pull_request_forks                      = false
    build_pull_request_ready_for_review           = false
    build_pull_request_labels_changed             = false
    build_pull_request_base_branch_changed        = false
    prefix_pull_request_fork_branch_names         = true
    filter_enabled                                = false
    pull_request_branch_filter_enabled            = false
    publish_commit_status                         = true
    publish_commit_status_per_step                = false
    separate_pull_request_statuses                = false
    publish_blocked_as_pending                    = false
    cancel_deleted_branch_builds                  = false
    skip_builds_for_existing_commits              = false
    skip_pull_request_builds_for_existing_commits = true
    ignore_default_branch_pull_requests           = false
    build_merge_group_checks_requested            = false
    cancel_when_merge_group_destroyed             = false
    use_merge_group_base_commit_for_git_diff_base = false
  }
}

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
  provider_settings = {
    # GitHub activities are disabled for this pipeline
    trigger_mode = "none"
  }
}

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
  provider_settings = {
    trigger_mode                                  = "code"
    build_branches                                = true
    build_pull_requests                           = true
    build_tags                                    = false
    build_pull_request_forks                      = false
    build_pull_request_ready_for_review           = false
    build_pull_request_labels_changed             = false
    build_pull_request_base_branch_changed        = false
    prefix_pull_request_fork_branch_names         = true
    filter_enabled                                = false
    pull_request_branch_filter_enabled            = false
    publish_commit_status                         = true
    publish_commit_status_per_step                = false
    separate_pull_request_statuses                = false
    publish_blocked_as_pending                    = false
    cancel_deleted_branch_builds                  = false
    skip_builds_for_existing_commits              = false
    skip_pull_request_builds_for_existing_commits = true
    ignore_default_branch_pull_requests           = false
    build_merge_group_checks_requested            = false
    cancel_when_merge_group_destroyed             = false
    use_merge_group_base_commit_for_git_diff_base = false
  }
}

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
  provider_settings = {
    trigger_mode                                  = "code"
    build_branches                                = true
    build_pull_requests                           = true
    build_tags                                    = false
    build_pull_request_forks                      = false
    build_pull_request_ready_for_review           = false
    build_pull_request_labels_changed             = false
    build_pull_request_base_branch_changed        = false
    prefix_pull_request_fork_branch_names         = true
    filter_enabled                                = false
    filter_condition                              = ""
    pull_request_branch_filter_enabled            = false
    pull_request_branch_filter_configuration      = ""
    publish_commit_status                         = false
    publish_commit_status_per_step                = false
    separate_pull_request_statuses                = false
    publish_blocked_as_pending                    = false
    cancel_deleted_branch_builds                  = false
    skip_builds_for_existing_commits              = false
    skip_pull_request_builds_for_existing_commits = true
    ignore_default_branch_pull_requests           = false
    build_merge_group_checks_requested            = false
    cancel_when_merge_group_destroyed             = false
    use_merge_group_base_commit_for_git_diff_base = false
  }
}
