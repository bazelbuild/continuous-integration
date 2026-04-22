terraform {
  backend "gcs" {
    bucket = "bazel-buildkite-tf-state"
    prefix = "bazel-trusted"
  }

  required_providers {
    buildkite = {
      source  = "buildkite/buildkite"
      version = "~> 1.0"
    }
  }
}

# This variable name must remain 'buildkite_api_token' for terraform to
# be able to recognize it (e.g. from TF_VAR_buildkite_api_token)
variable "buildkite_api_token" {
  description = "The API token used to authenticate with Buildkite"
  type        = string
  sensitive   = true
}

provider "buildkite" {
  api_token = var.buildkite_api_token
  organization = "bazel-trusted"
}
