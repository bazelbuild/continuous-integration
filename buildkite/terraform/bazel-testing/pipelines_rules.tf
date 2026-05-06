resource "buildkite_pipeline" "rules-apple-darwin" {
  name       = "rules_apple :darwin:"
  repository = "https://github.com/bazelbuild/rules_apple.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "/bin/bash -c 'set -euo pipefail; python3 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload'"
      ]
    }
  })
  default_branch             = "master"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
  provider_settings = {
    # GitHub activities are disabled for this pipeline
    trigger_mode = "none"
  }
}

