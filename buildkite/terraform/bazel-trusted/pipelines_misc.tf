resource "buildkite_pipeline" "update-git-mirror-tar-ball" {
  name           = "Update git mirror tar ball"
  repository     = "https://github.com/bazelbuild/continuous-integration.git"
  description    = "Update the git mirrors (gs://bazel-git-mirror/bazelbuild-mirror.{tar,zip}) used when building VM image"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "cd ./gitbundle",
        "sudo apt-get update && sudo apt-get install -y jq",
        "./gitbundle.sh"
      ],
      label = "Creating git mirror tar ball",
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

resource "buildkite_pipeline" "mirror-404-artifacts-for-bazel" {
  name           = "Mirror 404 artifacts for Bazel"
  repository     = "https://github.com/bazelbuild/continuous-integration.git"
  description    = "See https://github.com/bazelbuild/continuous-integration/pull/2386"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {
      BUILDKITE_API_TOKEN = "bkua_133f21c87527e7e20bae543f9d950c0c455fe1fa"
    },
    steps = {
      commands = [
        "cd buildkite",
        "python3 mirror_404_downloads.py"
      ],
      label = ":mirror: Mirror missing artifacts",
      image = "gcr.io/bazel-public/ubuntu2204"
    }
  })
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

resource "buildkite_pipeline" "bcr-integrity" {
  name           = "BCR Integrity"
  repository     = "https://github.com/bazelbuild/bazel-central-registry.git"
  description    = "Calculate integrity value of source archive (for testing java_tools releases)"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/java-tools-testing/pipelines/bcr-integrity.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
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

resource "buildkite_pipeline" "create-linux-vm-image" {
  name           = "Create Linux VM image"
  repository     = "https://github.com/bazelbuild/continuous-integration.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {
      BAZEL_TEST_VM_NAMES = "bk-testing-docker,bk-testing-docker-arm64"
      BAZEL_VM_NAMES      = "bk-docker,bk-docker-arm64"
    },
    steps = {
      commands = [
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/publish-vm-image.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
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

resource "buildkite_pipeline" "collect-infra-ci-metrics" {
  name           = "Collect Infra CI-Metrics"
  repository     = "https://github.com/bazelbuild/continuous-integration.git"
  description    = "Bazel's Continuous Integration Setup"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "cd buildkite",
        "pip install pyyaml requests google-cloud-kms google-cloud-bigquery",
        "python3 collect_infra_metrics.py"
      ],
      label = ":chart_with_upwards_trend: Collect Infra CI-Metrics"
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

resource "buildkite_pipeline" "create-linux-docker-images" {
  name                       = "Create Linux Docker Images"
  repository                 = "https://github.com/bazelbuild/continuous-integration.git"
  default_branch             = "master"
  steps                      = "---\nsteps:\n  - command: |-\n      docker builder prune -a -f\n      cd buildkite/docker\n      [ \"$BUILDKITE_BRANCH\" = \"master\" ] || [ \"$BUILDKITE_BRANCH\" = \"testing\" ] && git checkout $BUILDKITE_BRANCH\n      echo \"--- Building docker images...\"\n      ./build.sh\n      echo \"--- Pushing docker images...\"\n      ./push.sh\n    label: \":pipeline: Create images\"\n    agents:\n      - \"queue=default\""
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

resource "buildkite_pipeline" "docgen-bazel-website" {
  name           = "DocGen: Bazel-website"
  repository     = "https://github.com/bazelbuild/bazel-website.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/bazel-docgen.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
      ],
      label = ":pipeline:"
    }
  })
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

resource "buildkite_pipeline" "create-windows-vm-image" {
  name           = "Create Windows VM image"
  repository     = "https://github.com/bazelbuild/continuous-integration.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {
      BAZEL_TEST_VM_NAMES = "bk-testing-windows"
      BAZEL_VM_NAMES      = "bk-windows"
    },
    steps = {
      commands = [
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/publish-vm-image.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
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

resource "buildkite_pipeline" "docgen-bazel-blog" {
  name           = "DocGen: Bazel-blog"
  repository     = "https://github.com/bazelbuild/bazel-blog.git"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/bazel-docgen.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
      ],
      label = ":pipeline:"
    }
  })
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
    trigger_mode                                  = "code"
    build_branches                                = true
    build_pull_requests                           = false
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

resource "buildkite_pipeline" "bcr-postsubmit" {
  name           = "BCR Postsubmit"
  repository     = "https://github.com/bazelbuild/bazel-central-registry.git"
  description    = "Tasks to run after merging a change for the Bazel Central Registry"
  default_branch = "main"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazel-central-registry/bcr_postsubmit.py\" -o bcr_postsubmit.py",
        "python3.6 bcr_postsubmit.py"
      ],
      label = ":pipeline:"
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
    build_pull_requests                           = false
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

resource "buildkite_pipeline" "docker-update" {
  name           = "Docker update"
  repository     = "https://github.com/bazelbuild/continuous-integration.git"
  description    = "Build and publish docker container for new Bazel LTS releases"
  default_branch = "master"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/docker-update.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
      ],
      label = ":pipeline:",
      image = "gcr.io/bazel-public/ubuntu2404"
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

resource "buildkite_pipeline" "pcloudy-test" {
  name                       = "pcloudy test"
  repository                 = "https://github.com/bazelbuild/bazel.git"
  default_branch             = "master"
  steps                      = "# Enter your pipeline's YAML step configuration:\n\n# This default command changes the pipeline of a running build by uploading a configuration file.\n# https://buildkite.com/docs/agent/v3/cli-pipeline\n# For more information on different step types, toggle open the step guides\n\nsteps:\n  - agents: {queue: arm64}\n    command: ['touch foo', 'buildkite-agent artifact upload foo']\n    label: 'Debug ubuntu arm64'\n    plugins:\n      docker#v3.8.0:\n        always-pull: false\n        environment: [ANDROID_HOME, ANDROID_NDK_HOME, BUILDKITE_ARTIFACT_UPLOAD_DESTINATION, GOOGLE_APPLICATION_CREDENTIALS]\n        image: gcr.io/bazel-public/ubuntu2004\n        network: host\n        privileged: true\n        propagate-environment: false\n        propagate-uid-gid: true\n        volumes: ['/etc/group:/etc/group:ro', '/etc/passwd:/etc/passwd:ro', '/etc/shadow:/etc/shadow:ro',\n          '/opt/android-ndk-r15c:/opt/android-ndk-r15c:ro', '/opt/android-ndk-r25b:/opt/android-ndk-r25b:ro',\n          '/opt/android-sdk-linux:/opt/android-sdk-linux:ro', '/var/lib/buildkite-agent:/var/lib/buildkite-agent',\n          '/var/lib/gitmirrors:/var/lib/gitmirrors:ro', '/var/run/docker.sock:/var/run/docker.sock']"
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

resource "buildkite_pipeline" "docgen-bazel" {
  name           = "DocGen: Bazel"
  repository     = "https://github.com/bazelbuild/bazel.git"
  default_branch = "5.1-docs-fixes"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {},
    steps = {
      commands = [
        "curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/bazel-docgen.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"
      ],
      label = ":pipeline:"
    }
  })
  allow_rebuilds             = true
  branch_configuration       = "5.1-docs-fixes"
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

resource "buildkite_pipeline" "bazel-ssl-certificate-checker" {
  name                       = "Bazel SSL Certificate Checker"
  repository                 = "https://github.com/bazelbuild/bazel.git"
  description                = "a fast, scalable, multi-language and extensible build system"
  default_branch             = "master"
  steps                      = "---\nsteps:\n  - command: |-\n      python3 .github/scripts/check_ssl.py\n    label: \":lock: SSL Certificate Checker\"\n    agents:\n      - \"queue=default\""
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
