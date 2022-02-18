terraform {
  backend "gcs" {
    bucket  = "bazel-buildkite-tf-state"
    prefix  = "bazel"
  }

  required_providers {
    buildkite = {
      source = "buildkite/buildkite"
      version = "0.5.0"
    }
  }
}

provider "buildkite" {
  # can also be set from env: BUILDKITE_API_TOKEN
  #api_token = ""
  organization = "bazel"
}

resource "buildkite_pipeline" "fwe-inc-test" {
  name = "fwe inc test"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = jsondecode("{\"USE_BAZELISK_MIGRATE\": \"true\"}"), steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/fweikert/continuous-integration/inc/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py bazel_downstream_pipeline --test_incompatible_flags --http_config=https://raw.githubusercontent.com/bazelbuild/bazel/master/.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "bcr-postsubmit" {
  name = "BCR Postsubmit"
  repository = "https://github.com/bazelbuild/bazel-central-registry.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazel-central-registry/bcr_postsubmit.py\" -o bcr_postsubmit.py", "python3.6 bcr_postsubmit.py"] } })
  description = "The postsubmit for the Bazel Central Registry"
  default_branch = "main"
  branch_configuration = "main"
  skip_intermediate_builds = true
  cancel_intermediate_builds = true
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "bazel-sheriffs" }]
  provider_settings {
    trigger_mode = "code"
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "bcr-presubmit" {
  name = "BCR Presubmit"
  repository = "https://github.com/bazelbuild/bazel-central-registry.git"
  steps = templatefile("pipeline.yml.tpl", { envs = jsondecode("{\"USE_BAZEL_VERSION\": \"last_green\"}"), steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py\" -o bazelci.py", "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazel-central-registry/bcr_presubmit.py\" -o bcr_presubmit.py", "python3.6 bcr_presubmit.py bcr_presubmit | tee /dev/tty | buildkite-agent pipeline upload "] } })
  description = "The presubmit for adding new Bazel module into the Bazel Central Registry"
  default_branch = "main"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "bazel" }, { access_level = "MANAGE_BUILD_AND_READ", slug = "bazel-sheriffs" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
    publish_commit_status_per_step = true
  }
}

resource "buildkite_pipeline" "limdor-bazel-examples" {
  name = "limdor/bazel-examples"
  repository = "https://github.com/limdor/bazel-examples"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "rules-qt" }, { access_level = "MANAGE_BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
    publish_blocked_as_pending = true
  }
}

resource "buildkite_pipeline" "intellij-ue-plugin" {
  name = "IntelliJ UE plugin"
  repository = "https://github.com/bazelbuild/intellij.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/intellij-ue.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  description = "Tests the Bazel IntelliJ plugin with IntelliJ IDEA Ultimate"
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "btwiuse-k0s" {
  name = "btwiuse/k0s"
  repository = "https://github.com/btwiuse/k0s"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
  }
}

resource "buildkite_pipeline" "bcsgh-utilities" {
  name = "bcsgh/utilities"
  repository = "https://github.com/bcsgh/utilities"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bcsgh" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "bcsgh-tbd" {
  name = "bcsgh/tbd"
  repository = "https://github.com/bcsgh/tbd"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bcsgh" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "bcsgh-tbd-http" {
  name = "bcsgh/tbd-http"
  repository = "https://github.com/bcsgh/tbd-http"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bcsgh" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "bcsgh-stl-to-ps" {
  name = "bcsgh/stl-to-ps"
  repository = "https://github.com/bcsgh/stl-to-ps"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bcsgh" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
  }
}

resource "buildkite_pipeline" "bcsgh-bazel-rules" {
  name = "bcsgh/bazel_rules"
  repository = "https://github.com/bcsgh/bazel_rules"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bcsgh" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "bcsgh-bash-history-db" {
  name = "bcsgh/bash_history_db"
  repository = "https://github.com/bcsgh/bash_history_db"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bcsgh" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "distributed-point-functions" {
  name = "Distributed Point Functions"
  repository = "https://github.com/google/distributed_point_functions.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "googlers" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "cargo-raze" {
  name = "Cargo-Raze"
  repository = "https://github.com/google/cargo-raze.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "main"
  skip_intermediate_builds = true
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_ready_for_review = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "rules-qt" {
  name = "rules_qt"
  repository = "https://github.com/justbuchanan/bazel_rules_qt"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "googlers" }, { access_level = "BUILD_AND_READ", slug = "rules-qt" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
    publish_blocked_as_pending = true
  }
}

resource "buildkite_pipeline" "grpc-grpc-web" {
  name = "grpc/grpc-web"
  repository = "https://github.com/grpc/grpc-web"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "grpc" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
}

resource "buildkite_pipeline" "grpc-grpc" {
  name = "grpc/grpc"
  repository = "https://github.com/grpc/grpc"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "grpc" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
  }
}

resource "buildkite_pipeline" "dagger-query" {
  name = "dagger-query"
  repository = "https://github.com/googleinterns/dagger-query.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  description = ":dagger_knife:"
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "dagger-query" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
    publish_blocked_as_pending = true
  }
}

resource "buildkite_pipeline" "rules-pkg" {
  name = "rules_pkg"
  repository = "https://github.com/bazelbuild/rules_pkg.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"], label = "setup", artifact_paths = ["**/distro/rules_pkg*tar.tz"] } })
  default_branch = "main"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "rules-pkg" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "bazel-auto-sheriff-face-with-cowboy-hat" {
  name = "Bazel Auto Sheriff :face_with_cowboy_hat:"
  repository = "https://github.com/bazelbuild/continuous-integration.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["cd buildkite", "python3.6 bazel_auto_sheriff.py"], label = ":male-police-officer: :female-police-officer: :police_car:" } })
  description = "A pipeline to do most of work for the Bazel Green Team"
  default_branch = "master"
  team = [{ access_level = "READ_ONLY", slug = "bazel" }, { access_level = "MANAGE_BUILD_AND_READ", slug = "bazel-sheriffs" }]
}

resource "buildkite_pipeline" "github-dot-com-jmillikin-rules-ragel" {
  name = "github.com/jmillikin/rules_ragel"
  repository = "https://github.com/jmillikin/rules_ragel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "trunk"
  team = [{ access_level = "BUILD_AND_READ", slug = "jmillikinrules-ragel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status_per_step = true
    separate_pull_request_statuses = true
  }
}

resource "buildkite_pipeline" "github-dot-com-jmillikin-rules-flex" {
  name = "github.com/jmillikin/rules_flex"
  repository = "https://github.com/jmillikin/rules_flex.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "trunk"
  team = [{ access_level = "BUILD_AND_READ", slug = "jmillikinrules-flex" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
    publish_commit_status_per_step = true
    separate_pull_request_statuses = true
  }
}

resource "buildkite_pipeline" "github-dot-com-jmillikin-rules-bison" {
  name = "github.com/jmillikin/rules_bison"
  repository = "https://github.com/jmillikin/rules_bison.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "trunk"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "jmillikinrules-bison" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
    publish_commit_status_per_step = true
    separate_pull_request_statuses = true
  }
}

resource "buildkite_pipeline" "rules-postcss" {
  name = "rules_postcss"
  repository = "https://github.com/bazelbuild/rules_postcss.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "rules-postcss" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
    publish_commit_status_per_step = true
    separate_pull_request_statuses = true
  }
}

resource "buildkite_pipeline" "github-dot-com-googleapis-google-cloud-cpp" {
  name = "github.com/googleapis/google-cloud-cpp"
  repository = "https://github.com/googleapis/google-cloud-cpp.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "main"
  branch_configuration = "!gh-pages"
  team = [{ access_level = "BUILD_AND_READ", slug = "github-dot-comgoogleapisgoogle-cloud-cpp" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status_per_step = true
    separate_pull_request_statuses = true
  }
}

resource "buildkite_pipeline" "github-dot-com-brightspace-rules-csharp" {
  name = "github.com/brightspace/rules_csharp"
  repository = "https://github.com/Brightspace/rules_csharp.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "github-dot-combrightspacerules-csharp" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
    publish_commit_status_per_step = true
    separate_pull_request_statuses = true
  }
}

resource "buildkite_pipeline" "github-dot-com-jmillikin-rules-m4" {
  name = "github.com/jmillikin/rules_m4"
  repository = "https://github.com/jmillikin/rules_m4.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "trunk"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "github-dot-comjmillikinrules-m4" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
    publish_commit_status_per_step = true
    separate_pull_request_statuses = true
    publish_blocked_as_pending = true
  }
}

resource "buildkite_pipeline" "stardoc" {
  name = "Stardoc"
  repository = "https://github.com/bazelbuild/stardoc.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_tags = true
    publish_commit_status = true
    publish_commit_status_per_step = true
  }
}

resource "buildkite_pipeline" "rules-boost" {
  name = "rules_boost"
  repository = "https://github.com/nelhage/rules_boost.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "rules-boost" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "grpc-ecosystem-grpc-gateway" {
  name = "grpc-ecosystem/grpc-gateway"
  repository = "https://github.com/grpc-ecosystem/grpc-gateway.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "grpc-ecosystem" }, { access_level = "MANAGE_BUILD_AND_READ", slug = "googlers" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status_per_step = true
    separate_pull_request_statuses = true
  }
}

resource "buildkite_pipeline" "rules-proto" {
  name = "rules_proto"
  repository = "https://github.com/bazelbuild/rules_proto.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "rules-proto" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
    publish_commit_status_per_step = true
    separate_pull_request_statuses = true
  }
}

resource "buildkite_pipeline" "bazel-gazelle" {
  name = "Bazel Gazelle"
  repository = "https://github.com/bazelbuild/bazel-gazelle.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
    publish_commit_status_per_step = true
    separate_pull_request_statuses = true
  }
}

resource "buildkite_pipeline" "rules-proto-grpc-rules-proto-grpc" {
  name = "rules-proto-grpc/rules_proto_grpc"
  repository = "https://github.com/rules-proto-grpc/rules_proto_grpc.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "rules-proto-grpcrules-proto-grpc" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
    separate_pull_request_statuses = true
  }
}

resource "buildkite_pipeline" "rules-haskell-haskell" {
  name = "rules_haskell :haskell:"
  repository = "https://github.com/tweag/rules_haskell.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "rules-haskell" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
    publish_commit_status_per_step = true
    separate_pull_request_statuses = true
  }
}

resource "buildkite_pipeline" "google-bazel-platforms-presubmit" {
  name = "Google Bazel Platforms Presubmit"
  repository = "https://bazel.googlesource.com/platforms.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "googlers" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
}

resource "buildkite_pipeline" "bazel-platforms-bazel" {
  name = "Bazel Platforms :bazel:"
  repository = "https://github.com/bazelbuild/platforms.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "main"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "googlers" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "sandboxed-api" {
  name = "Sandboxed API"
  repository = "https://github.com/google/sandboxed-api.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "main"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "googlers" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "google-rules-java-presubmit" {
  name = "Google rules_java Presubmit"
  repository = "https://bazel.googlesource.com/rules_java.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "googlers" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
}

resource "buildkite_pipeline" "starlark" {
  name = "Starlark"
  repository = "https://github.com/bazelbuild/starlark.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "bazelbuildstarlark" }, { access_level = "MANAGE_BUILD_AND_READ", slug = "googlers" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "rules-java-java" {
  name = "rules_java :java:"
  repository = "https://github.com/bazelbuild/rules_java.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "googlers" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
    publish_commit_status_per_step = true
    separate_pull_request_statuses = true
  }
}

resource "buildkite_pipeline" "remote-apis-sdks" {
  name = "remote-apis-sdks"
  repository = "https://github.com/bazelbuild/remote-apis-sdks.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_tags = true
    publish_commit_status = true
    publish_commit_status_per_step = true
    separate_pull_request_statuses = true
    publish_blocked_as_pending = true
  }
}

resource "buildkite_pipeline" "ash2k-bazel-tools" {
  name = "ash2k/bazel-tools"
  repository = "https://github.com/ash2k/bazel-tools.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  skip_intermediate_builds = true
  team = [{ access_level = "BUILD_AND_READ", slug = "ash2kbazel-tools" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    build_tags = true
    publish_commit_status = true
    publish_commit_status_per_step = true
    separate_pull_request_statuses = true
    publish_blocked_as_pending = true
  }
}

resource "buildkite_pipeline" "bazel-codelabs" {
  name = "Bazel Codelabs"
  repository = "https://github.com/bazelbuild/codelabs.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
    separate_pull_request_statuses = true
  }
}

resource "buildkite_pipeline" "abseil-python" {
  name = "Abseil Python"
  repository = "https://github.com/abseil/abseil-py.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/abseil-py.yml?$(date +%s) | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "main"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
}

resource "buildkite_pipeline" "abseil-c-plus-plus" {
  name = "Abseil C++"
  repository = "https://github.com/abseil/abseil-cpp.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/abseil-cpp.yml?$(date +%s) | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
}

resource "buildkite_pipeline" "flogger" {
  name = "Flogger"
  repository = "https://github.com/google/flogger.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/flogger.yml?$(date +%s) | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
}

resource "buildkite_pipeline" "upb" {
  name = "upb"
  repository = "https://github.com/protocolbuffers/upb.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }, { access_level = "MANAGE_BUILD_AND_READ", slug = "upb" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    separate_pull_request_statuses = true
  }
}

resource "buildkite_pipeline" "envoy" {
  name = "Envoy"
  repository = "https://github.com/envoyproxy/envoy.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "main"
  team = [{ access_level = "BUILD_AND_READ", slug = "envoy" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
}

resource "buildkite_pipeline" "kythe" {
  name = "Kythe"
  repository = "https://github.com/kythe/kythe.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "googlers" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
    separate_pull_request_statuses = true
  }
}

resource "buildkite_pipeline" "bazel-bench" {
  name = "bazel-bench"
  repository = "https://github.com/bazelbuild/bazel-bench.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
    publish_commit_status_per_step = true
    separate_pull_request_statuses = true
  }
}

resource "buildkite_pipeline" "continuous-integration" {
  name = "continuous-integration"
  repository = "https://github.com/bazelbuild/continuous-integration.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/continuous-integration.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"] } })
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "googlers" }, { access_level = "BUILD_AND_READ", slug = "bazel" }, { access_level = "MANAGE_BUILD_AND_READ", slug = "bazel-sheriffs" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
    separate_pull_request_statuses = true
    pull_request_branch_filter_configuration = "master"
  }
}

resource "buildkite_pipeline" "rules-jvm-external-examples" {
  name = "rules_jvm_external - examples"
  repository = "https://github.com/bazelbuild/rules_jvm_external.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/rules_jvm_external/master/.bazelci/examples.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  description = "Example projects in rules_jvm_external"
  default_branch = "master"
  skip_intermediate_builds = true
  cancel_intermediate_builds = true
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }, { access_level = "MANAGE_BUILD_AND_READ", slug = "android-team" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_tags = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "vscode-bazel-vs-bazel" {
  name = "vscode-bazel :vs: :bazel:"
  repository = "https://github.com/bazelbuild/vscode-bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }, { access_level = "MANAGE_BUILD_AND_READ", slug = "googlers" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
    publish_commit_status_per_step = true
    publish_blocked_as_pending = true
  }
}

resource "buildkite_pipeline" "apple-support-darwin" {
  name = "apple_support :darwin:"
  repository = "https://github.com/bazelbuild/apple_support.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  branch_configuration = "!test_* !upstream"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "apple-team" }, { access_level = "BUILD_AND_READ", slug = "googlers" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
    publish_commit_status_per_step = true
    separate_pull_request_statuses = true
    publish_blocked_as_pending = true
  }
}

resource "buildkite_pipeline" "bazelisk-plus-incompatible-flags" {
  name = "Bazelisk + Incompatible flags"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = jsondecode("{\"USE_BAZELISK_MIGRATE\": \"true\"}"), steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py bazel_downstream_pipeline --test_incompatible_flags --http_config=https://raw.githubusercontent.com/bazelbuild/bazel/master/.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  description = "Use bazelisk --migrate to test incompatible flags with downstream projects@last_green_commit"
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }, { access_level = "BUILD_AND_READ", slug = "downstream-pipeline-triggerers" }, { access_level = "MANAGE_BUILD_AND_READ", slug = "bazel-sheriffs" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "bazel-bazel-examples" {
  name = "Bazel :bazel: Examples"
  repository = "https://github.com/bazelbuild/examples.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "main"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "googlers" }, { access_level = "BUILD_AND_READ", slug = "bazel" }, { access_level = "MANAGE_BUILD_AND_READ", slug = "bazel-sheriffs" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "mobile-devx-tools" {
  name = "Mobile DevX Tools"
  repository = "https://github.com/google/devx-tools.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/google/devx-tools/master/.continuous_integration/postsubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  description = "Tools used at Google for mobile development and testing"
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }, { access_level = "MANAGE_BUILD_AND_READ", slug = "android-team" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "stackb-rules-proto" {
  name = "stackb/rules_proto"
  repository = "https://github.com/stackb/rules_proto.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "v2_prerelease"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }, { access_level = "BUILD_AND_READ", slug = "googlers" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status_per_step = true
    separate_pull_request_statuses = true
  }
}

resource "buildkite_pipeline" "flatbuffers" {
  name = "FlatBuffers"
  repository = "https://github.com/google/flatbuffers.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }, { access_level = "MANAGE_BUILD_AND_READ", slug = "googlers" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
    separate_pull_request_statuses = true
  }
}

resource "buildkite_pipeline" "cloud-robotics-core" {
  name = "Cloud Robotics Core"
  repository = "https://github.com/googlecloudrobotics/core.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/cloud-robotics.yml?$(date +%s) | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
}

resource "buildkite_pipeline" "bazelisk" {
  name = "Bazelisk"
  repository = "https://github.com/bazelbuild/bazelisk.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/config.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "tulsi-bazel-darwin" {
  name = "Tulsi :bazel: :darwin:"
  repository = "https://github.com/bazelbuild/tulsi.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  branch_configuration = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "apple-team" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
    publish_commit_status_per_step = true
  }
}

resource "buildkite_pipeline" "rules-cc" {
  name = "rules_cc"
  repository = "https://github.com/bazelbuild/rules_cc.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "main"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
    separate_pull_request_statuses = true
  }
}

resource "buildkite_pipeline" "google-rules-cc-presubmit" {
  name = "Google rules_cc Presubmit"
  repository = "https://bazel.googlesource.com/rules_cc.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "main"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }, { access_level = "BUILD_AND_READ", slug = "googlers" }]
}

resource "buildkite_pipeline" "rules-swift-swift" {
  name = "rules_swift :swift:"
  repository = "https://github.com/bazelbuild/rules_swift.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  branch_configuration = "!test_* !upstream"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "apple-team" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
    publish_commit_status_per_step = true
    separate_pull_request_statuses = true
    publish_blocked_as_pending = true
  }
}

resource "buildkite_pipeline" "bazel-at-head-plus-disabled" {
  name = "Bazel@HEAD + Disabled"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py bazel_downstream_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/bazel/master/.bazelci/presubmit.yml --test_disabled_projects | tee /dev/tty | buildkite-agent pipeline upload"] } })
  description = "Test disabled downstream projects to see if they are already fixed."
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "bazel-sheriffs" }, { access_level = "BUILD_AND_READ", slug = "downstream-pipeline-triggerers" }, { access_level = "READ_ONLY", slug = "bazel" }]
}

resource "buildkite_pipeline" "culprit-finder" {
  name = "Culprit Finder"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = jsondecode("{\"NEEDS_CLEAN\": \"1\"}"), steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/culprit_finder.py?$(date +%s)\" -o culprit_finder.py", "python3.6 culprit_finder.py culprit_finder | tee /dev/tty | buildkite-agent pipeline upload"] } })
  description = "Find out which commit broke a project on specific platform"
  default_branch = "master"
  team = [{ access_level = "READ_ONLY", slug = "bazel" }, { access_level = "MANAGE_BUILD_AND_READ", slug = "bazel-sheriffs" }]
}

resource "buildkite_pipeline" "rules-dotnet-edge" {
  name = "rules_dotnet :edge:"
  repository = "https://github.com/bazelbuild/rules_dotnet.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    build_pull_request_ready_for_review = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    build_tags = true
    publish_commit_status = true
    publish_blocked_as_pending = true
  }
}

resource "buildkite_pipeline" "rules-webtesting-saucelabs" {
  name = "rules_webtesting :saucelabs:"
  repository = "https://github.com/bazelbuild/rules_webtesting.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "rules-webtesting" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "bazel-bazel-github-presubmit" {
  name = "Bazel :bazel: Github Presubmit"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  branch_configuration = "!master !release-*"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
    publish_commit_status_per_step = true
  }
}

resource "buildkite_pipeline" "rules-android" {
  name = "rules_android"
  repository = "https://github.com/bazelbuild/rules_android.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/rules_android/master/.bazelci/postsubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  description = "Android rules for Bazel"
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }, { access_level = "MANAGE_BUILD_AND_READ", slug = "android-team" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "rules-foreign-cc" {
  name = "rules_foreign_cc"
  repository = "https://github.com/bazelbuild/rules_foreign_cc.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/config.yaml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "main"
  branch_configuration = "main"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "bazel-sheriffs" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_ready_for_review = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    build_tags = true
    publish_commit_status = true
    publish_blocked_as_pending = true
  }
}

resource "buildkite_pipeline" "cartographer" {
  name = "Cartographer"
  repository = "https://github.com/googlecartographer/cartographer.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
  }
}

resource "buildkite_pipeline" "rules-jvm-external" {
  name = "rules_jvm_external"
  repository = "https://github.com/bazelbuild/rules_jvm_external.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  description = "Resolve and fetch artifacts transitively from Maven repositories"
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "android-team" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_tags = true
    publish_commit_status = true
    publish_commit_status_per_step = true
  }
}

resource "buildkite_pipeline" "android-testing" {
  name = "Android Testing"
  repository = "https://github.com/googlesamples/android-testing.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=bazelci/buildkite-pipeline.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  description = "https://github.com/googlesamples/android-testing#experimental-bazel-support"
  default_branch = "main"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "android-team" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status_per_step = true
    separate_pull_request_statuses = true
    publish_blocked_as_pending = true
  }
}

resource "buildkite_pipeline" "intellij-plugin-aspect" {
  name = "IntelliJ Plugin Aspect"
  repository = "https://github.com/bazelbuild/intellij.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/aspect.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "android-studio-plugin" {
  name = "Android Studio Plugin"
  repository = "https://github.com/bazelbuild/intellij.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/android-studio.yml --monitor_flaky_tests=true | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "bazel-remote-cache" {
  name = "Bazel Remote Cache"
  repository = "https://github.com/buchgr/bazel-remote.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "buchgrbazel-remote" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "rules-apple-darwin" {
  name = "rules_apple :darwin:"
  repository = "https://github.com/bazelbuild/rules_apple.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  branch_configuration = "!test_* !upstream"
  skip_intermediate_builds = true
  skip_intermediate_builds_branch_filter = "!master"
  cancel_intermediate_builds = true
  cancel_intermediate_builds_branch_filter = "!master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "apple-team" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    cancel_deleted_branch_builds = true
    publish_commit_status = true
    publish_commit_status_per_step = true
    separate_pull_request_statuses = true
    publish_blocked_as_pending = true
  }
}

resource "buildkite_pipeline" "bazel-integration-testing" {
  name = "Bazel integration testing"
  repository = "https://github.com/bazelbuild/bazel-integration-testing.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "bazel-skylib" {
  name = "Bazel skylib"
  repository = "https://github.com/bazelbuild/bazel-skylib.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "main"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "buildfarm-farmer" {
  name = "Buildfarm :farmer:"
  repository = "https://github.com/bazelbuild/bazel-buildfarm.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "main"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "rules-kotlin-kotlin" {
  name = "rules_kotlin :kotlin:"
  repository = "https://github.com/bazelbuild/rules_kotlin.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "rules-kotlin" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "google-bazel-presubmit" {
  name = "Google Bazel Presubmit"
  repository = "https://bazel.googlesource.com/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "bazel-sheriffs" }, { access_level = "BUILD_AND_READ", slug = "googlers" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
}

resource "buildkite_pipeline" "rules-docker-docker" {
  name = "rules_docker :docker:"
  repository = "https://github.com/bazelbuild/rules_docker.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "rules-sass" {
  name = "rules_sass"
  repository = "https://github.com/bazelbuild/rules_sass.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "rules-rust-rustlang" {
  name = "rules_rust :rustlang:"
  repository = "https://github.com/bazelbuild/rules_rust.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "main"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "rust" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "rules-d" {
  name = "rules_d"
  repository = "https://github.com/bazelbuild/rules_d.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "google-logging" {
  name = "Google Logging"
  repository = "https://github.com/google/glog.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "googlers" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "gerrit" {
  name = "Gerrit"
  repository = "https://gerrit.googlesource.com/gerrit.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/gerrit.yml?$(date +%s) | tee /dev/tty | buildkite-agent pipeline upload"] } })
  description = "Triggered every 4 hours"
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
}

resource "buildkite_pipeline" "bazel-toolchains" {
  name = "Bazel toolchains"
  repository = "https://github.com/bazelbuild/bazel-toolchains.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
    publish_blocked_as_pending = true
  }
}

resource "buildkite_pipeline" "clion-plugin" {
  name = "CLion plugin"
  repository = "https://github.com/bazelbuild/intellij.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/clion.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "intellij-plugin" {
  name = "IntelliJ plugin"
  repository = "https://github.com/bazelbuild/intellij.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/intellij.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  description = "Tests the Bazel IntelliJ plugin with IntelliJ IDEA Community Edition"
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "tensorflow" {
  name = "TensorFlow"
  repository = "https://github.com/tensorflow/tensorflow.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/tensorflow.yml?$(date +%s) | tee /dev/tty | buildkite-agent pipeline upload"] } })
  description = "Triggered every 4 hours"
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "tensorflow" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
}

resource "buildkite_pipeline" "bazel-at-head-plus-downstream" {
  name = "Bazel@HEAD + Downstream"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py bazel_downstream_pipeline --file_config=.bazelci/postsubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  description = "Test Bazel@HEAD + downstream projects@last_green_commit"
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "bazel-sheriffs" }, { access_level = "BUILD_AND_READ", slug = "downstream-pipeline-triggerers" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
}

resource "buildkite_pipeline" "rules-scala-scala" {
  name = "rules_scala :scala:"
  repository = "https://github.com/bazelbuild/rules_scala.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "rules-jsonnet" {
  name = "rules_jsonnet"
  repository = "https://github.com/bazelbuild/rules_jsonnet.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "rules-gwt" {
  name = "rules_gwt"
  repository = "https://github.com/bazelbuild/rules_gwt.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "rules-groovy" {
  name = "rules_groovy"
  repository = "https://github.com/bazelbuild/rules_groovy.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "rules-nodejs-nodejs" {
  name = "rules_nodejs :nodejs:"
  repository = "https://github.com/bazelbuild/rules_nodejs.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "stable"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "re2" {
  name = "re2"
  repository = "https://github.com/google/re2.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/re2.yml?$(date +%s) | tee /dev/tty | buildkite-agent pipeline upload"] } })
  description = "Triggered every 4 hours"
  default_branch = "main"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
  }
}

resource "buildkite_pipeline" "buildtools" {
  name = "Buildtools"
  repository = "https://github.com/bazelbuild/buildtools.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
    publish_blocked_as_pending = true
  }
}

resource "buildkite_pipeline" "protobuf" {
  name = "Protobuf"
  repository = "https://github.com/google/protobuf.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/protobuf.yml?$(date +%s) | tee /dev/tty | buildkite-agent pipeline upload"] } })
  description = "Triggered every 4 hours"
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
  }
}

resource "buildkite_pipeline" "rules-perl" {
  name = "rules_perl"
  repository = "https://github.com/bazelbuild/rules_perl.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "main"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "rules-k8s-k8s" {
  name = "rules_k8s :k8s:"
  repository = "https://github.com/bazelbuild/rules_k8s.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "rules-go-golang" {
  name = "rules_go :golang:"
  repository = "https://github.com/bazelbuild/rules_go.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "rules-go" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "rules-closure-closure-compiler" {
  name = "rules_closure :closure-compiler:"
  repository = "https://github.com/bazelbuild/rules_closure.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "rules-appengine-appengine" {
  name = "rules_appengine :appengine:"
  repository = "https://github.com/bazelbuild/rules_appengine.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "bazel-watcher" {
  name = "Bazel watcher"
  repository = "https://github.com/bazelbuild/bazel-watcher.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "rules-python-python" {
  name = "rules_python :python:"
  repository = "https://github.com/bazelbuild/rules_python.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "main"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "subpar" {
  name = "Subpar"
  repository = "https://github.com/google/subpar.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/subpar.yml?$(date +%s) | tee /dev/tty | buildkite-agent pipeline upload"] } })
  description = "Triggered every 4 hours"
  default_branch = "master"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
  }
}

resource "buildkite_pipeline" "bazel-bazel" {
  name = "Bazel :bazel:"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/postsubmit.yml --monitor_flaky_tests=true | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  branch_configuration = "master release-*"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "bazel-sheriffs" }, { access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "bazel-lib" {
  name = "bazel-lib"
  repository = "https://github.com/aspect-build/bazel-lib.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "main"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    filter_enabled = false
    build_pull_requests = true
    pull_request_branch_filter_enabled = false
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_ready_for_review = false
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = false
    build_tags = false
    cancel_deleted_branch_builds = false
    publish_commit_status = true
    publish_blocked_as_pending = false
    publish_commit_status_per_step = false
    separate_pull_request_statuses = false
  }
}

resource "buildkite_pipeline" "rules-license" {
  name = "rules_license"
  repository = "https://github.com/bazelbuild/rules_license.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "main"
  team = [{ access_level = "BUILD_AND_READ", slug = "bazel" }]
  provider_settings {
    trigger_mode = "code"
    filter_enabled = false
    build_pull_requests = true
    pull_request_branch_filter_enabled = false
    skip_pull_request_builds_for_existing_commits = true
    build_pull_request_ready_for_review = false
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    build_branches = false
    build_tags = false
    cancel_deleted_branch_builds = false
    publish_commit_status = true
    publish_blocked_as_pending = false
    publish_commit_status_per_step = false
    separate_pull_request_statuses = false
  }
}
