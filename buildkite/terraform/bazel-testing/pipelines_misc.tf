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
  provider_settings = {
      # GitHub activities are disabled for this pipeline
      trigger_mode = "none"
    }
}

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
    filter_enabled                                = true
    filter_condition                              = "build.pull_request.base_branch =~ /master/"
    pull_request_branch_filter_enabled            = false
    pull_request_branch_filter_configuration      = ""
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
  provider_settings = {
      # GitHub activities are disabled for this pipeline
      trigger_mode = "none"
    }
}

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
  provider_settings = {
      # GitHub activities are disabled for this pipeline
      trigger_mode = "none"
    }
}

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
  provider_settings = {
      # GitHub activities are disabled for this pipeline
      trigger_mode = "none"
    }
}

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
