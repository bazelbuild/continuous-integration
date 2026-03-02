resource "buildkite_pipeline" "rules-kotlin-green-publish" {
  name                       = "rules_kotlin green publish"
  repository                 = "git@github.com:bazelbuild/rules_kotlin.git"
  description                = "A pipeline to build rules_kotlin post-merge, and if green, publish a tag and attach the executables"
  default_branch             = "master"
  steps                      = "steps:\n  - command: \"echo 'Hello world!'\"\n"
  allow_rebuilds             = true
  branch_configuration       = "master"
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
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

resource "buildkite_pipeline" "rules-proto-grpc-rules-proto-grpc" {
  name           = "rules-proto-grpc/rules_proto_grpc"
  repository     = "https://github.com/rules-proto-grpc/rules_proto_grpc.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "github-dot-com-brightspace-rules-csharp" {
  name           = "github.com/brightspace/rules_csharp"
  repository     = "https://github.com/Brightspace/rules_csharp.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-qt" {
  name           = "rules_qt"
  repository     = "https://github.com/justbuchanan/bazel_rules_qt"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-apple-darwin" {
  name           = "rules_apple :darwin:"
  repository     = "https://github.com/bazelbuild/rules_apple.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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
    publish_commit_status_per_step                = true
    separate_pull_request_statuses                = true
    publish_blocked_as_pending                    = true
    cancel_deleted_branch_builds                  = true
    skip_builds_for_existing_commits              = false
    skip_pull_request_builds_for_existing_commits = true
    ignore_default_branch_pull_requests           = false
    build_merge_group_checks_requested            = false
    cancel_when_merge_group_destroyed             = false
    use_merge_group_base_commit_for_git_diff_base = false
  }
}

resource "buildkite_pipeline" "rules-scala-scala" {
  name           = "rules_scala :scala:"
  repository     = "https://github.com/bazel-contrib/rules_scala.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "google-rules-android-presubmit" {
  name           = "Google rules_android presubmit"
  repository     = "https://team.git.corp.google.com/mobile-ninjas-releaser/rules_android"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-cc" {
  name           = "rules_cc"
  repository     = "https://github.com/bazelbuild/rules_cc.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-groovy" {
  name           = "rules_groovy"
  repository     = "https://github.com/bazelbuild/rules_groovy.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "github-dot-com-jmillikin-rules-m4" {
  name           = "github.com/jmillikin/rules_m4"
  repository     = "https://github.com/jmillikin/rules_m4.git"
  default_branch = "trunk"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-kotlin-kotlin" {
  name           = "rules_kotlin :kotlin:"
  repository     = "https://github.com/bazelbuild/rules_kotlin.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-python-python" {
  name           = "rules_python :python:"
  repository     = "https://github.com/bazel-contrib/rules_python.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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
    skip_builds_for_existing_commits              = false
    skip_pull_request_builds_for_existing_commits = true
    ignore_default_branch_pull_requests           = false
    build_merge_group_checks_requested            = false
    cancel_when_merge_group_destroyed             = false
    use_merge_group_base_commit_for_git_diff_base = false
  }
}

resource "buildkite_pipeline" "rules-k8s-k8s" {
  name           = "rules_k8s :k8s:"
  repository     = "https://github.com/bazelbuild/rules_k8s.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-webtesting-saucelabs" {
  name           = "rules_webtesting :saucelabs:"
  repository     = "https://github.com/bazelbuild/rules_webtesting.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-android" {
  name           = "rules_android"
  repository     = "https://github.com/bazelbuild/rules_android.git"
  description    = "Android rules for Bazel"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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
    skip_builds_for_existing_commits              = false
    skip_pull_request_builds_for_existing_commits = true
    ignore_default_branch_pull_requests           = false
    build_merge_group_checks_requested            = false
    cancel_when_merge_group_destroyed             = false
    use_merge_group_base_commit_for_git_diff_base = false
  }
}

resource "buildkite_pipeline" "rules-platform" {
  name           = "rules_platform"
  repository     = "https://github.com/bazelbuild/rules_platform.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "google-rules-java-presubmit" {
  name           = "Google rules_java Presubmit"
  repository     = "https://bazel.googlesource.com/rules_java.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {
      DISABLE_BAZEL_DIFF = "1"
    }
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

resource "buildkite_pipeline" "rules-docker-docker" {
  name           = "rules_docker :docker:"
  repository     = "https://github.com/bazelbuild/rules_docker.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "google-rules-cc-presubmit" {
  name           = "Google rules_cc Presubmit"
  repository     = "https://bazel.googlesource.com/rules_cc.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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
  provider_settings          = null
  branch_configuration       = null
  cluster_id                 = null
  color                      = null
  default_team_id            = null
  emoji                      = null
  pipeline_template_id       = null
}

resource "buildkite_pipeline" "rules-testing" {
  name           = "rules_testing"
  repository     = "https://github.com/bazelbuild/rules_testing.git"
  description    = "Tests for https://github.com/bazelbuild/rules_testing"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-nodejs-nodejs" {
  name           = "rules_nodejs :nodejs:"
  repository     = "https://github.com/bazel-contrib/rules_nodejs.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "stackb-rules-proto" {
  name           = "stackb/rules_proto"
  repository     = "https://github.com/stackb/rules_proto.git"
  default_branch = "v2_prerelease"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-closure-closure-compiler" {
  name           = "rules_closure :closure-compiler:"
  repository     = "https://github.com/bazelbuild/rules_closure.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-appengine-appengine" {
  name           = "rules_appengine :appengine:"
  repository     = "https://github.com/bazelbuild/rules_appengine.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-go-golang" {
  name           = "rules_go :golang:"
  repository     = "https://github.com/bazel-contrib/rules_go.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-license" {
  name           = "rules_license"
  repository     = "https://github.com/bazelbuild/rules_license.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-sass" {
  name           = "rules_sass"
  repository     = "https://github.com/bazelbuild/rules_sass.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "github-dot-com-jmillikin-rules-flex" {
  name           = "github.com/jmillikin/rules_flex"
  repository     = "https://github.com/jmillikin/rules_flex.git"
  default_branch = "trunk"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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
    publish_commit_status                         = true
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

resource "buildkite_pipeline" "rules-java-java" {
  name           = "rules_java :java:"
  repository     = "https://github.com/bazelbuild/rules_java.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-boost" {
  name           = "rules_boost"
  repository     = "https://github.com/nelhage/rules_boost.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-swift-swift" {
  name           = "rules_swift :swift:"
  repository     = "https://github.com/bazelbuild/rules_swift.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "github-dot-com-jmillikin-rules-bison" {
  name           = "github.com/jmillikin/rules_bison"
  repository     = "https://github.com/jmillikin/rules_bison.git"
  default_branch = "trunk"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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
    publish_commit_status                         = true
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

resource "buildkite_pipeline" "rules-jsonnet" {
  name           = "rules_jsonnet"
  repository     = "https://github.com/bazel-contrib/rules_jsonnet.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-graalvm" {
  name           = "rules_graalvm"
  repository     = "https://github.com/sgammon/rules_graalvm.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-proto" {
  name           = "rules_proto"
  repository     = "https://github.com/bazelbuild/rules_proto.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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
    publish_commit_status                         = true
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

resource "buildkite_pipeline" "rules-gwt" {
  name           = "rules_gwt"
  repository     = "https://github.com/bazelbuild/rules_gwt.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-rust-rustlang" {
  name           = "rules_rust :rustlang:"
  repository     = "https://github.com/bazelbuild/rules_rust.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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
    skip_builds_for_existing_commits              = false
    skip_pull_request_builds_for_existing_commits = true
    ignore_default_branch_pull_requests           = false
    build_merge_group_checks_requested            = false
    cancel_when_merge_group_destroyed             = false
    use_merge_group_base_commit_for_git_diff_base = false
  }
}

resource "buildkite_pipeline" "rules-dotnet-edge" {
  name           = "rules_dotnet :edge:"
  repository     = "https://github.com/bazel-contrib/rules_dotnet.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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
    build_tags                                    = true
    build_pull_request_forks                      = true
    build_pull_request_ready_for_review           = true
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
    skip_pull_request_builds_for_existing_commits = false
    ignore_default_branch_pull_requests           = false
    build_merge_group_checks_requested            = false
    cancel_when_merge_group_destroyed             = false
    use_merge_group_base_commit_for_git_diff_base = false
  }
}

resource "buildkite_pipeline" "rules-perl" {
  name           = "rules_perl"
  repository     = "https://github.com/bazel-contrib/rules_perl.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "github-dot-com-jmillikin-rules-ragel" {
  name           = "github.com/jmillikin/rules_ragel"
  repository     = "https://github.com/jmillikin/rules_ragel.git"
  default_branch = "trunk"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-pkg" {
  name           = "rules_pkg"
  repository     = "https://github.com/bazelbuild/rules_pkg.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      label          = "setup",
      artifact_paths = ["**/distro/rules_pkg*tar.tz"],
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
    skip_builds_for_existing_commits              = false
    skip_pull_request_builds_for_existing_commits = true
    ignore_default_branch_pull_requests           = false
    build_merge_group_checks_requested            = false
    cancel_when_merge_group_destroyed             = false
    use_merge_group_base_commit_for_git_diff_base = false
  }
}

resource "buildkite_pipeline" "rules-haskell-haskell" {
  name           = "rules_haskell :haskell:"
  repository     = "https://github.com/tweag/rules_haskell.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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
    publish_commit_status                         = true
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

resource "buildkite_pipeline" "rules-jvm-external-examples" {
  name           = "rules_jvm_external - examples"
  repository     = "https://github.com/bazel-contrib/rules_jvm_external.git"
  description    = "Example projects in rules_jvm_external"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --file_config=.bazelci/examples.yml | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "rules-foreign-cc" {
  name           = "rules_foreign_cc"
  repository     = "https://github.com/bazel-contrib/rules_foreign_cc.git"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --file_config=.bazelci/config.yaml | tee /dev/tty | buildkite-agent pipeline upload"
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
    build_tags                                    = true
    build_pull_request_forks                      = true
    build_pull_request_ready_for_review           = true
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

resource "buildkite_pipeline" "rules-postcss" {
  name           = "rules_postcss"
  repository     = "https://github.com/bazelbuild/rules_postcss.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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
    publish_commit_status                         = true
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

resource "buildkite_pipeline" "rules-android-ndk" {
  name           = "rules_android_ndk"
  repository     = "https://github.com/bazelbuild/rules_android_ndk.git"
  description    = "Android NDK rules for Bazel"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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
    skip_builds_for_existing_commits              = false
    skip_pull_request_builds_for_existing_commits = true
    ignore_default_branch_pull_requests           = false
    build_merge_group_checks_requested            = false
    cancel_when_merge_group_destroyed             = false
    use_merge_group_base_commit_for_git_diff_base = false
  }
}

resource "buildkite_pipeline" "rules-jvm-external" {
  name           = "rules_jvm_external"
  repository     = "https://github.com/bazel-contrib/rules_jvm_external.git"
  description    = "Resolve and fetch artifacts transitively from Maven repositories"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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

resource "buildkite_pipeline" "rules-shell" {
  name           = "rules_shell"
  repository     = "https://github.com/bazelbuild/rules_shell.git"
  description    = "Shell rules for Bazel"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
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
    publish_commit_status                         = true
    publish_commit_status_per_step                = false
    separate_pull_request_statuses                = false
    publish_blocked_as_pending                    = false
    cancel_deleted_branch_builds                  = true
    skip_builds_for_existing_commits              = true
    skip_pull_request_builds_for_existing_commits = true
    ignore_default_branch_pull_requests           = false
    build_merge_group_checks_requested            = false
    cancel_when_merge_group_destroyed             = false
    use_merge_group_base_commit_for_git_diff_base = false
  }
}
