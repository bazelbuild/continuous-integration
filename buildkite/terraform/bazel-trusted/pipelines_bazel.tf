resource "buildkite_pipeline" "publish-bazel-binaries-platform" {
  name           = "Publish Bazel binaries (platform)"
  repository     = "https://github.com/bazelbuild/bazel.git"
  description    = "master"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/publish_bin_platform/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py bazel_publish_binaries_pipeline --http_config=https://raw.githubusercontent.com/meteorcloudy/bazel/publish_bin_platform/.bazelci/build_bazel_binaries.yml | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "bazel-custom-release" {
  name           = "Bazel Custom Release"
  repository     = "https://github.com/bazelbuild/bazel.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/bazel-custom-release.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
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

resource "buildkite_pipeline" "build-embedded-minimized-jdk" {
  name           = "Build embedded (minimized) JDK"
  repository     = "https://bazel.googlesource.com/bazel.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/build-embedded-minimized-jdk.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
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
  provider_settings          = null
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
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/java_tools-binaries.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
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

resource "buildkite_pipeline" "bazel-release-arm64" {
  name                       = "Bazel Release (arm64)"
  repository                 = "https://github.com/bazelbuild/bazel.git"
  default_branch             = "master"
  steps                      = file("bazel-release-arm64.yml")
  allow_rebuilds             = true
  branch_configuration       = "release-* 0.* 1.* 2.* 3.*"
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

resource "buildkite_pipeline" "bazel-bench-binaries" {
  name           = "Bazel Bench Binaries"
  repository     = "https://github.com/bazelbuild/bazel-bench.git"
  default_branch = "report-binary"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        # "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        # "curl -sS \"https://raw.githubusercontent.com/joeleba/continuous-integration/turbine-bm/buildkite/bazel-bench/bazel_bench_binaries.py?$(date +%s)\" -o bazel_bench.py",
        # "python3.6 bazel_bench.py --date=\"$(date --date yesterday +%Y-%m-%d)\" --bucket=perf.bazel.build --bazel_bench_options=\"--runs=10\" --max_commits=7 --bazel_binaries=\"4ad8acd,cc0581c,a1a8651,ace1a32,5e62af9,0db7a28,6610b80,8c646de\" --report_name=\"turbine-bm\"",
        "which bq",
        "bq load --skip_leading_rows=1 --source_format=CSV bazel-public:bazel_bench.bazel_bench_daily gs://perf.bazel.build/bazel/2020/01/16/macos/perf_data.csv"
      ],
      label = ":pipeline:",
      retry = true
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

resource "buildkite_pipeline" "bazel-java-tools-updates" {
  name           = "Bazel java_tools updates"
  repository     = "https://github.com/bazelbuild/bazel.git"
  description    = "Make updates to Bazel during/after a java_tools release"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/java-tools-testing/pipelines/bazel-java_tools-updates.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
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
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/java_tools-release.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
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
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/publish-bazel-binaries.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
      ],
      label = ":pipeline:"
    }
  })
  allow_rebuilds             = true
  branch_configuration       = "master release-* 4.* 5.* 6.* 7.* 8.* 9.*"
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
    publish_blocked_as_pending                    = false
    cancel_deleted_branch_builds                  = false
    skip_builds_for_existing_commits              = false
    skip_pull_request_builds_for_existing_commits = true
    ignore_default_branch_pull_requests           = true
    build_merge_group_checks_requested            = false
    cancel_when_merge_group_destroyed             = false
    use_merge_group_base_commit_for_git_diff_base = false
  }
}

resource "buildkite_pipeline" "bazel-arm64" {
  name                       = "Bazel (arm64)"
  repository                 = "https://github.com/bazelbuild/bazel.git"
  default_branch             = "master"
  steps                      = file("bazel-arm64.yml")
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

resource "buildkite_pipeline" "bazel-bench-master-report-deprecated" {
  name           = "Bazel Bench Master Report - Deprecated"
  repository     = "https://github.com/bazelbuild/bazel-bench.git"
  description    = "Generates the daily combined performance report."
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "bazel run //report:generate_master_report -- --date=\"$(date --date yesterday +%Y-%m-%d)\"  --storage_bucket=perf.bazel.build --bigquery_table='bazel-public:bazel_bench.bazel_bench_daily' --upload_report=True",
        "gsutil cp gs://perf.bazel.build/all/\"$(date --date yesterday +%Y/%m/%d)\"/report.html gs://perf.bazel.build/all/report_latest.html"
      ],
      label = ":pipeline:",
      retry = true
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

resource "buildkite_pipeline" "bazel-release" {
  name           = "Bazel Release"
  repository     = "https://github.com/bazelbuild/bazel.git"
  default_branch = "release-8.1.0"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/bazel-release.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
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

resource "buildkite_pipeline" "java-tools-rc" {
  name           = "java_tools RC"
  repository     = "https://github.com/bazelbuild/bazel.git"
  description    = "Run create_java_tools_release.sh"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/java_tools-rc.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
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

resource "buildkite_pipeline" "bazel-bench-culprit-finder" {
  name           = "Bazel Bench Culprit Finder"
  repository     = "https://github.com/bazelbuild/bazel-bench.git"
  description    = "To find the exact commit that's responsible for a performance regression"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {
      BAZEL_COMMITS   = "9ec7d7b"
      DATE            = "2021-07-28"
      PROJECT_COMMITS = "9ec7d7b,4b3c740"
      REPORT_NAME     = "macos_bazel_reg20210728"
    },
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "curl -sS \"https://raw.githubusercontent.com/tjgq/continuous-integration/test/buildkite/bazel-bench/bazel_bench.py?$(date +%s)\" -o bazel_bench.py",
        "python3.6 bazel_bench.py --date=\"$DATE\" --projects=\"bazel\" --bucket=perf.bazel.build --bigquery_table='bazel-public:bazel_bench.bazel_bench_daily_test' --bazel_bench_options=\"--runs=5 --bazel_commits=$BAZEL_COMMITS --project_commits=$PROJECT_COMMITS --aggregate_json_profiles=False\" --max_commits=7 --report_name=$REPORT_NAME --upload_report"
      ],
      label = ":pipeline:",
      retry = true
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

resource "buildkite_pipeline" "bazel-bench-nightly-deprecated" {
  name           = "Bazel Bench Nightly - Deprecated"
  repository     = "https://github.com/bazelbuild/bazel-bench.git"
  description    = "Runs bazel-bench every night and records the performance of Bazel for each commits during that day."
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazel-bench/bazel_bench.py?$(date +%s)\" -o bazel_bench.py",
        "python3.6 bazel_bench.py --date=\"$(date --date yesterday +%Y-%m-%d)\" --bucket=perf.bazel.build --bigquery_table='bazel-public:bazel_bench.bazel_bench_daily' --bazel_bench_options=\"--runs=7\" --max_commits=7 --update_latest --upload_report"
      ],
      label = ":pipeline:",
      retry = true
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

resource "buildkite_pipeline" "bazel-bench-nightly-test" {
  name           = "Bazel Bench Nightly - Test"
  repository     = "https://github.com/bazelbuild/bazel-bench.git"
  description    = "A test playground for bazel bench nightly"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "curl -sS \"https://raw.githubusercontent.com/joeleba/continuous-integration/last-commit-prev-day/buildkite/bazel-bench/bazel_bench.py?$(date +%s)\" -o bazel_bench.py",
        "# python3.6 bazel_bench.py --date=\"$(date --date yesterday +%Y-%m-%d)\" --bucket=perf.bazel.build --bigquery_table='bazel-public:bazel_bench.bazel_bench_daily' --bazel_bench_options=\"--runs=7\" --max_commits=7 --update_latest --upload_report",
        "python3.6 bazel_bench.py --date=\"2020-02-15\" --bucket=perf.bazel.build --bigquery_table='bazel-public:bazel_bench.bazel_bench_daily_test' --bazel_bench_options=\"--runs=5\" --max_commits=7 --report_name=\"report\""
      ],
      label = ":pipeline:",
      retry = true
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
