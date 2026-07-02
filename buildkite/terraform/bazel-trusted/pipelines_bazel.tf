resource "buildkite_pipeline" "mirror-last-green-commit-for-bazel" {
  name           = "Mirror last green commit for Bazel"
  repository     = "https://github.com/bazelbuild/continuous-integration.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "gsutil cp gs://bazel-builds/last_green_commit/github.com/bazelbuild/bazel.git/publish-bazel-binaries gs://bazel-untrusted-builds/last_green_commit/github.com/bazelbuild/bazel.git/bazel-bazel"
      ],
      label = ":pipeline:",
      image = "gcr.io/bazel-public/ubuntu2204"
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

resource "buildkite_pipeline" "java-tools-binaries-java" {
  name           = "java_tools binaries :java:"
  repository     = "https://github.com/bazelbuild/bazel.git"
  description    = "Temporary pipeline for building java_tools binaries on all platforms"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "bash -c 'set -euo pipefail; curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/java_tools-binaries.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace'"
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
    trigger_mode                                  = "code"
    build_branches                                = false
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
    publish_commit_status                         = true
    publish_commit_status_per_step                = false
    separate_pull_request_statuses                = false
    publish_blocked_as_pending                    = true
    cancel_deleted_branch_builds                  = false
    skip_builds_for_existing_commits              = false
    skip_pull_request_builds_for_existing_commits = true
    ignore_default_branch_pull_requests           = false
    build_merge_group_checks_requested            = false
    cancel_when_merge_group_destroyed             = false
    use_merge_group_base_commit_for_git_diff_base = false
  }
}

resource "buildkite_pipeline" "bazel-java-tools-updates" {
  name           = "Bazel java_tools updates"
  repository     = "https://github.com/bazelbuild/bazel.git"
  description    = "Make updates to Bazel during/after a java_tools release"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "bash -c 'set -euo pipefail; curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/java-tools-testing/pipelines/bazel-java_tools-updates.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace'"
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

resource "buildkite_pipeline" "java-tools-release" {
  name           = "java_tools release"
  repository     = "https://github.com/bazelbuild/java_tools.git"
  description    = "Release java_tools"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "bash -c 'set -euo pipefail; curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/java_tools-release.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace'"
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

resource "buildkite_pipeline" "publish-bazel-binaries" {
  name           = "Publish Bazel binaries"
  repository     = "https://github.com/bazelbuild/bazel.git"
  description    = "Publish Bazel binaries to GCS (http://storage.googleapis.com/bazel-builds/metadata/latest.json)"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "bash -c 'set -euo pipefail; curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/publish-bazel-binaries.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace'"
      ],
      label = ":pipeline:"
    }
  })
  allow_rebuilds             = true
  branch_configuration       = "master release-* 7.* 8.* 9.* 10.* 11.* 12.*"
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
  cluster_id                 = null
  color                      = null
  default_team_id            = null
  emoji                      = null
  pipeline_template_id       = null
  provider_settings = {
    trigger_mode                                  = "code"
    build_branches                                = true
    build_pull_requests                           = false
    build_tags                                    = true
    build_pull_request_forks                      = false
    build_pull_request_ready_for_review           = false
    build_pull_request_labels_changed             = false
    build_pull_request_base_branch_changed        = false
    prefix_pull_request_fork_branch_names         = true
    filter_enabled                                = false
    filter_condition                              = ""
    pull_request_branch_filter_enabled            = false
    pull_request_branch_filter_configuration      = ""
    publish_commit_status                         = true
    publish_commit_status_per_step                = false
    separate_pull_request_statuses                = false
    publish_blocked_as_pending                    = true
    cancel_deleted_branch_builds                  = false
    skip_builds_for_existing_commits              = false
    skip_pull_request_builds_for_existing_commits = true
    ignore_default_branch_pull_requests           = true
    build_merge_group_checks_requested            = false
    cancel_when_merge_group_destroyed             = false
    use_merge_group_base_commit_for_git_diff_base = false
  }
}

resource "buildkite_pipeline" "bazel-release" {
  name           = "Bazel Release"
  repository     = "https://github.com/bazelbuild/bazel.git"
  default_branch = "release-8.1.0"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "bash -c 'set -euo pipefail; curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/bazel-release.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace'"
      ],
      label = ":pipeline:"
    }
  })
  allow_rebuilds             = true
  branch_configuration       = "*rc* 0.* 1.* 2.* 3.* 4.* 5.* 6.* 7.* 8.* 9.* 10.* 11.* 12.* 13.*"
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
  cluster_id                 = null
  color                      = null
  default_team_id            = null
  emoji                      = null
  pipeline_template_id       = null
  provider_settings = {
    trigger_mode                                  = "code"
    build_branches                                = true
    build_pull_requests                           = false
    build_tags                                    = true
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
    publish_blocked_as_pending                    = true
    cancel_deleted_branch_builds                  = false
    skip_builds_for_existing_commits              = false
    skip_pull_request_builds_for_existing_commits = true
    ignore_default_branch_pull_requests           = false
    build_merge_group_checks_requested            = false
    cancel_when_merge_group_destroyed             = false
    use_merge_group_base_commit_for_git_diff_base = false
  }
}

resource "buildkite_pipeline" "java-tools-rc" {
  name           = "java_tools RC"
  repository     = "https://github.com/bazelbuild/bazel.git"
  description    = "Run create_java_tools_release.sh"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "bash -c 'set -euo pipefail; curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/java_tools-rc.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace'"
      ],
      label = ":pipeline:",
      image = "gcr.io/bazel-public/ubuntu2004-java11"
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




