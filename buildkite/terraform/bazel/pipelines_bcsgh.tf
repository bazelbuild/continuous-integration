
resource "buildkite_pipeline" "bcsgh-bash-history-db" {
  name           = "bcsgh/bash_history_db"
  repository     = "https://github.com/bcsgh/bash_history_db"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
  provider_settings = {
    trigger_mode                                  = "code"
    build_branches                                = true
    build_pull_requests                           = true
    build_tags                                    = false
    publish_commit_status                         = true
    publish_commit_status_per_step                = false
    pull_request_branch_filter_enabled            = false
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks                      = false
    prefix_pull_request_fork_branch_names         = true
    separate_pull_request_statuses                = false
    publish_blocked_as_pending                    = false
  }
  branch_configuration = null
  cluster_id           = null
  color                = null
  default_team_id      = null
  emoji                = null
  pipeline_template_id = null
}

resource "buildkite_pipeline" "bcsgh-utilities" {
  name           = "bcsgh/utilities"
  repository     = "https://github.com/bcsgh/utilities"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "bcsgh-tbd" {
  name           = "bcsgh/tbd"
  repository     = "https://github.com/bcsgh/tbd"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "bcsgh-stl-to-ps" {
  name           = "bcsgh/stl-to-ps"
  repository     = "https://github.com/bcsgh/stl-to-ps"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "bcsgh-tbd-http" {
  name           = "bcsgh/tbd-http"
  repository     = "https://github.com/bcsgh/tbd-http"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "bcsgh-bazel-rules" {
  name           = "bcsgh/bazel_rules"
  repository     = "https://github.com/bcsgh/bazel_rules"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
  provider_settings = {
    trigger_mode                                  = "code"
    build_branches                                = true
    build_pull_requests                           = true
    build_tags                                    = false
    publish_commit_status                         = true
    publish_commit_status_per_step                = false
    pull_request_branch_filter_enabled            = false
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks                      = false
    prefix_pull_request_fork_branch_names         = true
    separate_pull_request_statuses                = false
    publish_blocked_as_pending                    = false
  }
  branch_configuration = null
  cluster_id           = null
  color                = null
  default_team_id      = null
  emoji                = null
  pipeline_template_id = null
}