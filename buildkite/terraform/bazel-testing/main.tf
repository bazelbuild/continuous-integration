terraform {
  backend "gcs" {
    bucket  = "bazel-buildkite-tf-state"
    prefix  = "bazel-testing"
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
  organization = "bazel-testing"
}

resource "buildkite_pipeline" "upb" {
  name = "upb"
  repository = "https://github.com/protocolbuffers/upb.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
}

resource "buildkite_pipeline" "bcr-presubmit" {
  name = "BCR Presubmit"
  repository = "https://github.com/meteorcloudy/bazel-central-registry.git"
  steps = templatefile("pipeline.yml.tpl", { envs = jsondecode("{\"USE_BAZEL_VERSION\": \"last_green\"}"), steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/pcloudy-bcr-test/buildkite/bazelci.py\" -o bazelci.py", "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/pcloudy-bcr-test/buildkite/bazel-central-registry/bcr_presubmit.py\" -o bcr_presubmit.py", "python3.6 bcr_presubmit.py bcr_presubmit"] } })
  description = "The presubmit for adding new Bazel module into the Bazel Central Registry"
  default_branch = "main"
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    build_pull_request_forks = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status_per_step = true
    publish_blocked_as_pending = true
    filter_enabled = true
    pull_request_branch_filter_configuration = "*@*"
    filter_condition = "build.pull_request.labels includes \"bcr-presubmit\""
  }
}

resource "buildkite_pipeline" "protobuf" {
  name = "Protobuf"
  repository = "https://github.com/protocolbuffers/protobuf.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/protobuf-postsubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
  }
}

resource "buildkite_pipeline" "intellij-plugin" {
  name = "IntelliJ plugin"
  repository = "https://github.com/bazelbuild/intellij.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/aspect.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
}

resource "buildkite_pipeline" "google-bazel-presubmit" {
  name = "Google Bazel Presubmit"
  repository = "https://bazel.googlesource.com/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
}

resource "buildkite_pipeline" "tulsi-bazel-darwin" {
  name = "Tulsi :bazel: :darwin:"
  repository = "https://github.com/bazelbuild/tulsi.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
}

resource "buildkite_pipeline" "apple-support-darwin" {
  name = "apple_support :darwin:"
  repository = "https://github.com/bazelbuild/apple_support.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
}

resource "buildkite_pipeline" "rules-apple-darwin" {
  name = "rules_apple :darwin:"
  repository = "https://github.com/bazelbuild/rules_apple.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
}

resource "buildkite_pipeline" "android-testing" {
  name = "Android Testing"
  repository = "https://github.com/googlesamples/android-testing.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=bazelci/buildkite-pipeline.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "main"
}

resource "buildkite_pipeline" "rules-swift-swift" {
  name = "rules_swift :swift:"
  repository = "https://github.com/bazelbuild/rules_swift.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
}

resource "buildkite_pipeline" "rules-scala-scala" {
  name = "rules_scala :scala:"
  repository = "https://github.com/bazelbuild/rules_scala.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
}

resource "buildkite_pipeline" "rules-groovy" {
  name = "rules_groovy"
  repository = "https://github.com/bazelbuild/rules_groovy.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
}

resource "buildkite_pipeline" "rules-rust-rustlang" {
  name = "rules_rust :rustlang:"
  repository = "https://github.com/bazelbuild/rules_rust.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "main"
}

resource "buildkite_pipeline" "rules-kotlin-kotlin" {
  name = "rules_kotlin :kotlin:"
  repository = "https://github.com/bazelbuild/rules_kotlin.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
}

resource "buildkite_pipeline" "rules-docker-docker" {
  name = "rules_docker :docker:"
  repository = "https://github.com/bazelbuild/rules_docker.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
}

resource "buildkite_pipeline" "rules-go-golang" {
  name = "rules_go :golang:"
  repository = "https://github.com/bazelbuild/rules_go.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
}

resource "buildkite_pipeline" "rules-nodejs-nodejs" {
  name = "rules_nodejs :nodejs:"
  repository = "https://github.com/bazelbuild/rules_nodejs.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --monitor_flaky_tests=true | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "stable"
}

resource "buildkite_pipeline" "publish-bazel-binaries" {
  name = "Publish Bazel binaries"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/pipelines/publish-bazel-binaries.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"] } })
  description = "Publish Bazel binaries to GCS (http://storage.googleapis.com/bazel-testing-builds/metadata/latest.json)"
  default_branch = "master"
  branch_configuration = "master"
}

resource "buildkite_pipeline" "bazelisk-plus-incompatible-flags" {
  name = "Bazelisk + Incompatible flags"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = jsondecode("{\"USE_BAZELISK_MIGRATE\": true}"), steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py bazel_downstream_pipeline | tee /dev/tty | buildkite-agent pipeline upload"] } })
  description = "Use bazelisk --migrate to test incompatible flags with downstream projects@last_green_commit"
  default_branch = "master"
}

resource "buildkite_pipeline" "bazel-at-head-plus-disabled" {
  name = "Bazel@HEAD + Disabled"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py bazel_downstream_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/bazel/master/.bazelci/presubmit.yml --test_disabled_projects | tee /dev/tty | buildkite-agent pipeline upload"] } })
  description = "Test disabled downstream projects to see if they are already fixed."
  default_branch = "master"
}

resource "buildkite_pipeline" "bazel-at-head-plus-downstream" {
  name = "Bazel@HEAD + Downstream"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py bazel_downstream_pipeline --http_config=https://raw.githubusercontent.com/bazelbuild/bazel/master/.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  description = "Test Bazel@HEAD + downstream projects@last_green_commit"
  default_branch = "master"
}

resource "buildkite_pipeline" "bazelisk" {
  name = "Bazelisk"
  repository = "https://github.com/bazelbuild/bazelisk.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/config.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  branch_configuration = "master"
}

resource "buildkite_pipeline" "bazel-bazel-github-presubmit" {
  name = "Bazel :bazel: Github Presubmit"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/presubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  branch_configuration = "!*"
}

resource "buildkite_pipeline" "bazel-bazel" {
  name = "Bazel :bazel:"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "python3.6 bazelci.py project_pipeline --file_config=.bazelci/postsubmit.yml | tee /dev/tty | buildkite-agent pipeline upload"] } })
  default_branch = "master"
  branch_configuration = "master release-*"
}
