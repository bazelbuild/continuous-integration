resource "buildkite_pipeline" "google-bazel-presubmit" {
  name       = "Google Bazel Presubmit"
  repository = "https://bazel.googlesource.com/bazel.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "/bin/bash -c 'set -euo pipefail; python3 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload'"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
}

resource "buildkite_pipeline" "fwe-test" {
  name       = "fwe-test"
  repository = "https://github.com/fweikert/bazel"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {
      LC_ALL = "en_US.UTF-8"
      ENABLE_METRICS_COLLECTION = "true"
    }
    steps = {
      commands = [
         "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
         "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/collect_metrics.py?$(date +%s)\" -o collect_metrics.py",
         "/bin/bash -c 'set -euo pipefail; python3 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/fweikert/bazel/refs/heads/qa/.bazelci/postsubmit.yml | tee /dev/tty | buildkite-agent pipeline upload'"
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
