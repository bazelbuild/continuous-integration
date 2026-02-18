resource "buildkite_pipeline" "rules-apple-darwin" {
  name       = "rules_apple :darwin:"
  repository = "https://github.com/bazelbuild/rules_apple.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "rules-swift-swift" {
  name       = "rules_swift :swift:"
  repository = "https://github.com/bazelbuild/rules_swift.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "rules-scala-scala" {
  name       = "rules_scala :scala:"
  repository = "https://github.com/bazelbuild/rules_scala.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "rules-groovy" {
  name       = "rules_groovy"
  repository = "https://github.com/bazelbuild/rules_groovy.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "rules-rust-rustlang" {
  name       = "rules_rust :rustlang:"
  repository = "https://github.com/bazelbuild/rules_rust.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "main"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
  provider_settings = {
      # GitHub activities are disabled for this pipeline
      trigger_mode = "none"
    }
}

resource "buildkite_pipeline" "rules-kotlin-kotlin" {
  name       = "rules_kotlin :kotlin:"
  repository = "https://github.com/bazelbuild/rules_kotlin.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "rules-go-golang" {
  name       = "rules_go :golang:"
  repository = "https://github.com/bazel-contrib/rules_go.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
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

resource "buildkite_pipeline" "rules-nodejs-nodejs" {
  name       = "rules_nodejs :nodejs:"
  repository = "https://github.com/bazelbuild/rules_nodejs.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline --monitor_flaky_tests=true | tee /dev/tty | buildkite-agent pipeline upload"
      ]
    }
  })
  default_branch             = "main"
  allow_rebuilds             = true
  cancel_intermediate_builds = false
  skip_intermediate_builds   = false
  tags                       = []
  provider_settings = {
      # GitHub activities are disabled for this pipeline
      trigger_mode = "none"
    }
}

resource "buildkite_pipeline" "rules-docker-docker" {
  name       = "rules_docker :docker:"
  repository = "https://github.com/bazelbuild/rules_docker.git"
  steps = templatefile("pipeline.yml.tpl", {
    envs = {}
    steps = {
      commands = [
        "curl -sS \"https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)\" -o bazelci.py",
        "python3.6 bazelci.py project_pipeline | tee /dev/tty | buildkite-agent pipeline upload"
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
