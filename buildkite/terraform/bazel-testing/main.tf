terraform {
  backend "gcs" {
    bucket = "bazel-buildkite-tf-state"
    prefix = "bazel-testing"
  }

  required_providers {
    buildkite = {
      source  = "buildkite/buildkite"
      version = "~> 1.0"
    }
  }
}

provider "buildkite" {
  # can also be set from env: BUILDKITE_API_TOKEN
  #api_token    = ""
  organization = "bazel-testing"
}