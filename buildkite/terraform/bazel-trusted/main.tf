terraform {
  backend "gcs" {
    bucket  = "bazel-buildkite-tf-state"
    prefix  = "bazel-trusted"
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
  organization = "bazel-trusted"
}

resource "buildkite_pipeline" "bazel-arm64" {
  name = "Bazel (arm64)"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = file("bazel-arm64.yml")
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

resource "buildkite_pipeline" "docgen-bazel-website" {
  name = "DocGen: Bazel-website"
  repository = "https://github.com/bazelbuild/bazel-website.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/bazel-docgen.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"] } })
  default_branch = "master"
  branch_configuration = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "bazel-docs" }]
  provider_settings {
    trigger_mode = "code"
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
  }
}

resource "buildkite_pipeline" "docgen-bazel-blog" {
  name = "DocGen: Bazel-blog"
  repository = "https://github.com/bazelbuild/bazel-blog.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/bazel-docgen.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"] } })
  default_branch = "master"
  branch_configuration = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "bazel-docs" }]
  provider_settings {
    trigger_mode = "code"
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
  }
}

resource "buildkite_pipeline" "docgen-bazel" {
  name = "DocGen: Bazel"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/bazel-docgen.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"] } })
  default_branch = "master"
  branch_configuration = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "bazel-docs" }]
  provider_settings {
    trigger_mode = "code"
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
  }
}

resource "buildkite_pipeline" "bazel-custom-release" {
  name = "Bazel Custom Release"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/bazel-custom-release.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"] } })
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "release-managers" }]
}

resource "buildkite_pipeline" "bazel-release-arm64" {
  name = "Bazel Release (arm64)"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = file("bazel-release-arm64.yml")
  default_branch = "master"
  branch_configuration = "release-* 0.* 1.* 2.* 3.*"
  team = [{ access_level = "READ_ONLY", slug = "release-managers" }]
  provider_settings {
    trigger_mode = "code"
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
    build_tags = true
  }
}

resource "buildkite_pipeline" "bazel-bench-master-report" {
  name = "Bazel Bench Master Report"
  repository = "https://github.com/bazelbuild/bazel-bench.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["python3 -m pip install -r third_party/requirements.txt", "python3 report/generate_master_report.py --date=\"$(date --date yesterday +%Y-%m-%d)\"  --storage_bucket=perf.bazel.build --bigquery_table='bazel-public:bazel_bench.bazel_bench_daily' --upload_report=True", "wait", "gsutil cp gs://perf.bazel.build/all/\"$(date --date yesterday +%Y/%m/%d)\"/report.html gs://perf.bazel.build/all/report_latest.html"], retry = true } })
  description = "Generates the daily combined performance report."
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "bazel-bench" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "bazel-bench-nightly-test" {
  name = "Bazel Bench Nightly - Test"
  repository = "https://github.com/bazelbuild/bazel-bench.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "curl -sS \"https://raw.githubusercontent.com/joeleba/continuous-integration/last-commit-prev-day/buildkite/bazel-bench/bazel_bench.py?$(date +%s)\" -o bazel_bench.py", "# python3.6 bazel_bench.py --date=\"$(date --date yesterday +%Y-%m-%d)\" --bucket=perf.bazel.build --bigquery_table='bazel-public:bazel_bench.bazel_bench_daily' --bazel_bench_options=\"--runs=7\" --max_commits=7 --update_latest --upload_report", "python3.6 bazel_bench.py --date=\"2020-02-15\" --bucket=perf.bazel.build --bigquery_table='bazel-public:bazel_bench.bazel_bench_daily_test' --bazel_bench_options=\"--runs=5\" --max_commits=7 --report_name=\"report\""], retry = true } })
  description = "A test playground for bazel bench nightly"
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "bazel-bench" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "bazel-bench-binaries" {
  name = "Bazel Bench Binaries"
  repository = "https://github.com/bazelbuild/bazel-bench.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["#curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "#curl -sS \"https://raw.githubusercontent.com/joeleba/continuous-integration/turbine-bm/buildkite/bazel-bench/bazel_bench_binaries.py?$(date +%s)\" -o bazel_bench.py", "#python3.6 bazel_bench.py --date=\"$(date --date yesterday +%Y-%m-%d)\" --bucket=perf.bazel.build --bazel_bench_options=\"--runs=10\" --max_commits=7 --bazel_binaries=\"4ad8acd,cc0581c,a1a8651,ace1a32,5e62af9,0db7a28,6610b80,8c646de\" --report_name=\"turbine-bm\"", "which bq", "bq load --skip_leading_rows=1 --source_format=CSV bazel-public:bazel_bench.bazel_bench_daily gs://perf.bazel.build/bazel/2020/01/16/macos/perf_data.csv"], retry = true } })
  default_branch = "report-binary"
  team = [{ access_level = "READ_ONLY", slug = "java-tools-team" }, { access_level = "MANAGE_BUILD_AND_READ", slug = "bazel-bench" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "bazel-bench-culprit-finder" {
  name = "Bazel Bench Culprit Finder"
  repository = "https://github.com/bazelbuild/bazel-bench.git"
  steps = templatefile("pipeline.yml.tpl", { envs = jsondecode("{\"DATE\": \"2021-07-28\", \"BAZEL_COMMITS\": \"9ec7d7b\", \"PROJECT_COMMITS\": \"9ec7d7b,4b3c740\", \"REPORT_NAME\": \"macos_bazel_reg20210728\"}"), steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "curl -sS \"https://raw.githubusercontent.com/joeleba/continuous-integration/master/buildkite/bazel-bench/bazel_bench.py?$(date +%s)\" -o bazel_bench.py", "python3.6 bazel_bench.py --date=\"$DATE\" --projects=\"bazel\" --bucket=perf.bazel.build --bigquery_table='bazel-public:bazel_bench.bazel_bench_daily_test' --bazel_bench_options=\"--runs=5 --bazel_commits=$BAZEL_COMMITS --project_commits=$PROJECT_COMMITS --aggregate_json_profiles=False\" --max_commits=7 --report_name=$REPORT_NAME --upload_report"], retry = true } })
  description = "To find the exact commit that's responsible for a performance regression"
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "bazel-bench" }]
}

resource "buildkite_pipeline" "bazel-bench-nightly" {
  name = "Bazel Bench Nightly"
  repository = "https://github.com/bazelbuild/bazel-bench.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py", "# curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazel-bench/bazel_bench.py?$(date +%s)\" -o bazel_bench.py", "curl -sS \"https://raw.githubusercontent.com/joeleba/continuous-integration/master/buildkite/bazel-bench/bazel_bench.py?$(date +%s)\" -o bazel_bench.py", "python3.6 bazel_bench.py --date=\"$(date --date yesterday +%Y-%m-%d)\" --bucket=perf.bazel.build --bigquery_table='bazel-public:bazel_bench.bazel_bench_daily' --bazel_bench_options=\"--runs=7\" --max_commits=7 --update_latest --upload_report"], retry = true } })
  description = "Runs bazel-bench every night and records the performance of Bazel for each commits during that day."
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "bazel-bench" }]
}

resource "buildkite_pipeline" "java-tools-binaries-java" {
  name = "java_tools binaries :java:"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/java_tools-binaries.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"] } })
  description = "Temporary pipeline for building java_tools binaries on all platforms"
  default_branch = "master"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "java-tools-team" }, { access_level = "READ_ONLY", slug = "everyone" }]
  provider_settings {
    trigger_mode = "code"
    build_pull_requests = true
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
    publish_commit_status = true
  }
}

resource "buildkite_pipeline" "bazel-release" {
  name = "Bazel Release"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/bazel-release.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"] } })
  default_branch = "0.21.0"
  branch_configuration = "release-* 0.* 1.* 2.* 3.* 4.* 5.* 6.*"
  team = [{ access_level = "MANAGE_BUILD_AND_READ", slug = "release-managers" }, { access_level = "READ_ONLY", slug = "everyone" }]
  provider_settings {
    trigger_mode = "code"
    skip_pull_request_builds_for_existing_commits = true
    prefix_pull_request_fork_branch_names = true
    build_branches = true
    build_tags = true
  }
}

resource "buildkite_pipeline" "publish-bazel-binaries" {
  name = "Publish Bazel binaries"
  repository = "https://github.com/bazelbuild/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/publish-bazel-binaries.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"] } })
  description = "Publish Bazel binaries to GCS (http://storage.googleapis.com/bazel-builds/metadata/latest.json)"
  default_branch = "master"
  branch_configuration = "master"
  team = [{ access_level = "READ_ONLY", slug = "everyone" }]
  provider_settings {
    trigger_mode = "code"
    build_branches = true
    build_tags = true
  }
}

resource "buildkite_pipeline" "build-embedded-minimized-jdk" {
  name = "Build embedded (minimized) JDK"
  repository = "https://bazel.googlesource.com/bazel.git"
  steps = templatefile("pipeline.yml.tpl", { envs = {}, steps = { commands = ["curl -s \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/pipelines/build-embedded-minimized-jdk.yml?$(date +%s)\" | tee /dev/tty | buildkite-agent pipeline upload --replace"] } })
  default_branch = "master"
  team = [{ access_level = "READ_ONLY", slug = "everyone" }]
}
