
resource "buildkite_pipeline" "flatbuffers" {
  name           = "FlatBuffers"
  repository     = "https://github.com/google/flatbuffers.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
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
    build_branches                                = false
    build_pull_requests                           = true
    build_tags                                    = false
    build_pull_request_forks                      = true
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

resource "buildkite_pipeline" "gerrit" {
  name           = "Gerrit"
  repository     = "https://gerrit.googlesource.com/gerrit.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/gerrit.yml?$(date +%s) | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
  provider_settings          = null
  branch_configuration       = null
  cluster_id                 = null
  color                      = null
  default_team_id            = null
  emoji                      = null
  pipeline_template_id       = null
}

resource "buildkite_pipeline" "abseil-python" {
  name           = "Abseil Python"
  repository     = "https://github.com/abseil/abseil-py.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/abseil-py.yml?$(date +%s) | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "envoy" {
  name           = "Envoy"
  repository     = "https://github.com/envoyproxy/envoy.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "cartographer" {
  name           = "Cartographer"
  repository     = "https://github.com/googlecartographer/cartographer.git"
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
    build_branches                                = false
    build_pull_requests                           = true
    build_tags                                    = false
    build_pull_request_forks                      = true
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

resource "buildkite_pipeline" "mobile-devx-tools" {
  name           = "Mobile DevX Tools"
  repository     = "https://github.com/google/devx-tools.git"
  description    = "Tools used at Google for mobile development and testing"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/google/devx-tools/master/.continuous_integration/postsubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"
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
    build_branches                                = false
    build_pull_requests                           = true
    build_tags                                    = false
    build_pull_request_forks                      = true
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

resource "buildkite_pipeline" "buildfarm-admin-farmer" {
  name                       = "Buildfarm Admin :farmer:"
  repository                 = "https://github.com/buildfarm/bfadmin.git"
  default_branch             = "main"
  steps                      = "---\nsteps:\n  - command: \".bazelci/test_bfadmin.sh\"\n    label: \"Build and Test\"\n    agents:\n      - \"queue=default\"\n"
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

resource "buildkite_pipeline" "re2" {
  name           = "re2"
  repository     = "https://github.com/google/re2.git"
  description    = "Triggered every 4 hours"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/re2.yml?$(date +%s) | tee /dev/tty | buildkite-agent pipeline upload"
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
    build_pull_request_forks                      = true
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

resource "buildkite_pipeline" "buildfarm-farmer" {
  name           = "Buildfarm :farmer:"
  repository     = "https://github.com/buildfarm/buildfarm.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
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
    build_pull_request_forks                      = true
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
    skip_builds_for_existing_commits              = true
    skip_pull_request_builds_for_existing_commits = true
    ignore_default_branch_pull_requests           = false
    build_merge_group_checks_requested            = false
    cancel_when_merge_group_destroyed             = false
    use_merge_group_base_commit_for_git_diff_base = false
  }
}

resource "buildkite_pipeline" "grpc-ecosystem-grpc-gateway" {
  name           = "grpc-ecosystem/grpc-gateway"
  repository     = "https://github.com/grpc-ecosystem/grpc-gateway.git"
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
    build_branches                                = false
    build_pull_requests                           = true
    build_tags                                    = false
    build_pull_request_forks                      = true
    build_pull_request_ready_for_review           = false
    build_pull_request_labels_changed             = false
    build_pull_request_base_branch_changed        = false
    prefix_pull_request_fork_branch_names         = true
    filter_enabled                                = false
    filter_condition                              = ""
    pull_request_branch_filter_enabled            = false
    pull_request_branch_filter_configuration      = ""
    publish_commit_status                         = false
    publish_commit_status_per_step                = true
    separate_pull_request_statuses                = true
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

resource "buildkite_pipeline" "android-studio-plugin" {
  name           = "Android Studio Plugin"
  repository     = "https://github.com/bazelbuild/intellij.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --file_config=.bazelci/android-studio.yml --monitor_flaky_tests=true | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  allow_rebuilds             = true
  branch_configuration       = "!google"
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
    build_pull_requests                           = true
    build_tags                                    = false
    build_pull_request_forks                      = true
    build_pull_request_ready_for_review           = false
    build_pull_request_labels_changed             = false
    build_pull_request_base_branch_changed        = false
    prefix_pull_request_fork_branch_names         = true
    filter_enabled                                = true
    filter_condition                              = "build.pull_request.base_branch != \"google\""
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

resource "buildkite_pipeline" "distributed-point-functions" {
  name           = "Distributed Point Functions"
  repository     = "https://github.com/google/distributed_point_functions.git"
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
    build_pull_request_forks                      = true
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

resource "buildkite_pipeline" "macos-infra-update" {
  name           = "MacOS infra update"
  repository     = "https://github.com/bazelbuild/bazel.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/fweikert/continuous-integration/macos-infra/pipelines/macos_infra_update.yml?$(date +%s) | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "grpc-grpc-web" {
  name           = "grpc/grpc-web"
  repository     = "https://github.com/grpc/grpc-web"
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
    # GitHub activities are disabled for this pipeline
    trigger_mode = "none"
  }
}

resource "buildkite_pipeline" "abseil-c-plus-plus" {
  name           = "Abseil C++"
  repository     = "https://github.com/abseil/abseil-cpp.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/abseil-cpp.yml?$(date +%s) | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "dagger-query" {
  name           = "dagger-query"
  repository     = "https://github.com/googleinterns/dagger-query.git"
  description    = ":dagger_knife:"
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
    build_branches                                = false
    build_pull_requests                           = true
    build_tags                                    = false
    build_pull_request_forks                      = true
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
    skip_pull_request_builds_for_existing_commits = false
    ignore_default_branch_pull_requests           = false
    build_merge_group_checks_requested            = false
    cancel_when_merge_group_destroyed             = false
    use_merge_group_base_commit_for_git_diff_base = false
  }
}

resource "buildkite_pipeline" "cloud-robotics-core" {
  name           = "Cloud Robotics Core"
  repository     = "https://github.com/googlecloudrobotics/core.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/cloud-robotics.yml?$(date +%s) | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "kythe" {
  name           = "Kythe"
  repository     = "https://github.com/kythe/kythe.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
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
    build_branches                                = false
    build_pull_requests                           = true
    build_tags                                    = false
    build_pull_request_forks                      = true
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
    separate_pull_request_statuses                = true
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

resource "buildkite_pipeline" "continuous-integration" {
  name           = "continuous-integration"
  repository     = "https://github.com/bazelbuild/continuous-integration.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/continuous-integration.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
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
    build_branches                                = false
    build_pull_requests                           = true
    build_tags                                    = false
    build_pull_request_forks                      = true
    build_pull_request_ready_for_review           = false
    build_pull_request_labels_changed             = true
    build_pull_request_base_branch_changed        = false
    prefix_pull_request_fork_branch_names         = true
    filter_enabled                                = true
    filter_condition                              = "build.pull_request.labels includes \"CI:run\" || build.branch !~ /.+:.+/"
    pull_request_branch_filter_enabled            = false
    pull_request_branch_filter_configuration      = "master"
    publish_commit_status                         = true
    publish_commit_status_per_step                = false
    separate_pull_request_statuses                = true
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

resource "buildkite_pipeline" "starlark" {
  name           = "Starlark"
  repository     = "https://github.com/bazelbuild/starlark.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
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
    build_branches                                = false
    build_pull_requests                           = true
    build_tags                                    = false
    build_pull_request_forks                      = true
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

resource "buildkite_pipeline" "android-testing" {
  name           = "Android Testing"
  repository     = "https://github.com/googlesamples/android-testing.git"
  description    = "https://github.com/googlesamples/android-testing#experimental-bazel-support"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --file_config=bazelci/buildkite-pipeline.yml | tee /dev/tty | buildkite-agent pipeline upload"
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
    build_pull_request_forks                      = true
    build_pull_request_ready_for_review           = false
    build_pull_request_labels_changed             = false
    build_pull_request_base_branch_changed        = false
    prefix_pull_request_fork_branch_names         = true
    filter_enabled                                = false
    filter_condition                              = ""
    pull_request_branch_filter_enabled            = false
    pull_request_branch_filter_configuration      = ""
    publish_commit_status                         = false
    publish_commit_status_per_step                = true
    separate_pull_request_statuses                = true
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

resource "buildkite_pipeline" "btwiuse-k0s" {
  name           = "btwiuse/k0s"
  repository     = "https://github.com/btwiuse/k0s"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "remote-apis-sdks" {
  name           = "remote-apis-sdks"
  repository     = "https://github.com/bazelbuild/remote-apis-sdks.git"
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
    build_branches                                = false
    build_pull_requests                           = true
    build_tags                                    = true
    build_pull_request_forks                      = true
    build_pull_request_ready_for_review           = false
    build_pull_request_labels_changed             = false
    build_pull_request_base_branch_changed        = false
    prefix_pull_request_fork_branch_names         = true
    filter_enabled                                = false
    filter_condition                              = ""
    pull_request_branch_filter_enabled            = false
    pull_request_branch_filter_configuration      = ""
    publish_commit_status                         = true
    publish_commit_status_per_step                = true
    separate_pull_request_statuses                = true
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

resource "buildkite_pipeline" "fwe-shard-test" {
  name           = "fwe shard test"
  repository     = "https://github.com/bazelbuild/bazel.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/fweikert/continuous-integration/bep/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py --script https://raw.githubusercontent.com/fweikert/continuous-integration/bep/buildkite/bazelci.py project_pipeline --print_shard_summary  | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "grpc-grpc" {
  name           = "grpc/grpc"
  repository     = "https://github.com/grpc/grpc"
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
    build_pull_request_forks                      = true
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

resource "buildkite_pipeline" "tools-android" {
  name           = "tools_android"
  repository     = "https://github.com/bazelbuild/tools_android.git"
  description    = "Tools for use with building Android apps with Bazel"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
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


resource "buildkite_pipeline" "bcr-presubmit" {
  name           = "BCR Presubmit"
  repository     = "https://github.com/bazelbuild/bazel-central-registry.git"
  description    = "The presubmit for adding new Bazel module into the Bazel Central Registry"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {
      USE_BAZEL_VERSION       = "latest",
      ENABLE_BAZELISK_MIGRATE = "1"
    },
    steps = {
      image = "gcr.io/bazel-public/ubuntu2204",
      commands = [
        "curl -q --noproxy '*' -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py\" -o bazelci.py",
        "curl -q --noproxy '*' -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazel-central-registry/bcr_presubmit.py\" -o bcr_presubmit.py",
        "python3 bcr_presubmit.py bcr_presubmit"
      ]
    }
  })
  allow_rebuilds             = true
  cancel_intermediate_builds = true
  skip_intermediate_builds   = true
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
    build_pull_request_forks                      = true
    build_pull_request_ready_for_review           = true
    build_pull_request_labels_changed             = true
    build_pull_request_base_branch_changed        = false
    prefix_pull_request_fork_branch_names         = true
    filter_enabled                                = false
    filter_condition                              = "(build.pull_request.labels includes \"skip-url-stability-check\") || (build.pull_request.labels includes \"presubmit-auto-run\")"
    pull_request_branch_filter_enabled            = false
    pull_request_branch_filter_configuration      = ""
    publish_commit_status                         = true
    publish_commit_status_per_step                = true
    separate_pull_request_statuses                = false
    publish_blocked_as_pending                    = false
    cancel_deleted_branch_builds                  = true
    skip_builds_for_existing_commits              = true
    skip_pull_request_builds_for_existing_commits = false
    ignore_default_branch_pull_requests           = false
    build_merge_group_checks_requested            = false
    cancel_when_merge_group_destroyed             = false
    use_merge_group_base_commit_for_git_diff_base = false
  }
}


resource "buildkite_pipeline" "apple-support-darwin" {
  name           = "apple_support :darwin:"
  repository     = "https://github.com/bazelbuild/apple_support.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  allow_rebuilds                           = true
  branch_configuration                     = "master bazel/*"
  cancel_intermediate_builds               = true
  cancel_intermediate_builds_branch_filter = "!master !bazel/*"
  skip_intermediate_builds                 = true
  skip_intermediate_builds_branch_filter   = "!master !bazel/*"
  tags                                     = []
  cluster_id                               = null
  color                                    = null
  default_team_id                          = null
  emoji                                    = null
  pipeline_template_id                     = null
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
    filter_enabled                                = false
    filter_condition                              = ""
    pull_request_branch_filter_enabled            = false
    pull_request_branch_filter_configuration      = ""
    publish_commit_status                         = true
    publish_commit_status_per_step                = true
    separate_pull_request_statuses                = true
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

resource "buildkite_pipeline" "culprit-finder" {
  name           = "Culprit Finder"
  repository     = "https://github.com/bazelbuild/bazel.git"
  description    = "Find out which commit broke a project on specific platform"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = jsondecode("{\"NEEDS_CLEAN\": \"1\"}"),
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/culprit_finder.py?$(date +%s)\" -o culprit_finder.py",
        "python3.6 culprit_finder.py culprit_finder | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "flogger" {
  name           = "Flogger"
  repository     = "https://github.com/google/flogger.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/flogger.yml?$(date +%s) | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "stardoc" {
  name           = "Stardoc"
  repository     = "https://github.com/bazelbuild/stardoc.git"
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
    build_branches                                = false
    build_pull_requests                           = true
    build_tags                                    = true
    build_pull_request_forks                      = true
    build_pull_request_ready_for_review           = false
    build_pull_request_labels_changed             = false
    build_pull_request_base_branch_changed        = false
    prefix_pull_request_fork_branch_names         = true
    filter_enabled                                = false
    filter_condition                              = ""
    pull_request_branch_filter_enabled            = false
    pull_request_branch_filter_configuration      = ""
    publish_commit_status                         = true
    publish_commit_status_per_step                = true
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

resource "buildkite_pipeline" "buildtools" {
  name                       = "Buildtools"
  repository                 = "https://github.com/bazelbuild/buildtools.git"
  default_branch             = "main"
  steps                      = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
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
    build_pull_request_forks                      = true
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

resource "buildkite_pipeline" "upb" {
  name           = "upb"
  repository     = "https://github.com/protocolbuffers/upb.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "cargo-raze" {
  name           = "Cargo-Raze"
  repository     = "https://github.com/google/cargo-raze.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = true
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

resource "buildkite_pipeline" "bzlmod-migration-tool" {
  name           = "bzlmod-migration-tool"
  repository     = "https://github.com/bazelbuild/bazel-central-registry.git"
  description    = "The central registry of Bazel modules for the Bzlmod external dependency system."
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --file_config=.bazelci/migration_tool_presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"
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
    build_pull_request_forks                      = true
    build_pull_request_ready_for_review           = false
    build_pull_request_labels_changed             = true
    build_pull_request_base_branch_changed        = false
    prefix_pull_request_fork_branch_names         = true
    filter_enabled                                = true
    filter_condition                              = "build.pull_request.labels includes \"migration-tool-testing\""
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

resource "buildkite_pipeline" "protobuf" {
  name           = "Protobuf"
  repository     = "https://github.com/google/protobuf.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
      "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"]
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
    build_pull_requests                           = false
    build_tags                                    = false
    build_pull_request_forks                      = true
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

resource "buildkite_pipeline" "subpar" {
  name           = "Subpar"
  repository     = "https://github.com/google/subpar.git"
  description    = "Triggered every 4 hours"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/subpar.yml?$(date +%s) | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "clion-plugin" {
  name           = "CLion plugin"
  repository     = "https://github.com/bazelbuild/intellij.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --file_config=.bazelci/clion.yml | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  allow_rebuilds             = true
  branch_configuration       = "!google"
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
    build_pull_requests                           = true
    build_tags                                    = false
    build_pull_request_forks                      = true
    build_pull_request_ready_for_review           = false
    build_pull_request_labels_changed             = false
    build_pull_request_base_branch_changed        = false
    prefix_pull_request_fork_branch_names         = true
    filter_enabled                                = true
    filter_condition                              = "build.pull_request.base_branch != \"google\""
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

resource "buildkite_pipeline" "sandboxed-api" {
  name           = "Sandboxed API"
  repository     = "https://github.com/google/sandboxed-api.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "crubit-presubmit" {
  name           = "Crubit Presubmit"
  repository     = "https://bazel.googlesource.com/crubit.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
  provider_settings          = null
  branch_configuration       = null
  cluster_id                 = null
  color                      = null
  default_team_id            = null
  emoji                      = null
  pipeline_template_id       = null
}

resource "buildkite_pipeline" "host-exec" {
  name                       = "host-exec"
  repository                 = "pull/14729/head"
  description                = "Migrate HOST to EXEC for Starlark rules"
  default_branch             = "master"
  steps                      = "steps:\n  - command: \"echo 'Hello world!'\"\n"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
  provider_settings          = null
  branch_configuration       = null
  cluster_id                 = null
  color                      = null
  default_team_id            = null
  emoji                      = null
  pipeline_template_id       = null
}

resource "buildkite_pipeline" "fwe-test" {
  name           = "fwe-test"
  repository     = "https://github.com/bazelbuild/bazel"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/fweikert/continuous-integration/pr2/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
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
    build_pull_request_forks                      = true
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

resource "buildkite_pipeline" "tensorflow" {
  name           = "TensorFlow"
  repository     = "https://github.com/tensorflow/tensorflow.git"
  description    = "Triggered every 4 hours"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/tensorflow.yml?$(date +%s) | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "crubit" {
  name           = "crubit"
  repository     = "https://github.com/google/crubit.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  allow_rebuilds             = true
  branch_configuration       = "main"
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
    build_pull_requests                           = true
    build_tags                                    = false
    build_pull_request_forks                      = true
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
    separate_pull_request_statuses                = true
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
