This directory contains terraform configuration files to manage pipelines on Buildkite.

```
terraform
|
|- bazel            # Configuration files for bazel
|- bazel-testing    # Configuration files for bazel-testing
```

The terraform [state](https://www.terraform.io/docs/language/state/index.html) is stored in GCS bucket `bazel-buildkite-tf-state` (non-public).

## Setup
Please follow these steps to setup your local terraform environment:
  1. Install [terraform](https://www.terraform.io/downloads.html).
  1. Install Google Cloud SDK and authenticate using application default credentials. Make sure you have permissions to access bucket `bazel-buildkite-tf-state`. Check [here](https://www.terraform.io/docs/language/settings/backends/gcs.html#authentication) for more details about authentication.
  1. Generate Buildkite API token by following this [doc](https://registry.terraform.io/providers/buildkite/buildkite/latest/docs). Make sure required scopes are selected and GraphQL is enabled.
  1. Use environment to allow `terraform` read the API token:
      ```
      export BUILDKITE_API_TOKEN=TOKEN
      ```
  1. Run `terraform init` in one of the configurtion directories, e.g. `terraform/bazel-testing`.

## Add new pipeline
  1. Add `buildkite_pipeline` resource, e.g.:
      ```
      resource "buildkite_pipeline" "android-testing" {
        name = "Android Testing"
        repository = "https://github.com/googlesamples/android-testing.git"
        steps = templatefile("pipeline.yml.tpl", { flags = ["--file_config=bazelci/buildkite-pipeline.yml"] })
      }
      ```
     You can check all available properties [here](https://registry.terraform.io/providers/buildkite/buildkite/latest/docs/resources/pipeline).
  1. Run `terraform plan` to preview the change.
  1. Run `terraform apply` to apply the change.

## Update managed pipeline
  1. Edit `buildkite_pipeline` resource.
  1. Run `terraform plan` to preview the change.
  1. Run `terraform apply` to apply the change.

## Import existing pipeline from Buildkite

  1. Add `buildkite_pipeline` resource, e.g.:
      ```
      resource "buildkite_pipeline" "foo" {
      }
      ```
      It is recommended to name the resource with the slug of existing pipeline.
  1. Find the existing pipeline ID. You can find it in the `GraphQL API Integration` section of the `Pipeline Settings` of that pipeline on Buildkite. e.g. `UGlwZWxpbmUtLS0xYmJmYmM2NS0wMzE5LTQxMDMtOGY2Yy0zOGQ3MDQyYzVlZjc=`
  1. Bind the resource with existing pipeline:
      ```
      terraform import buildkite_pipeline.foo PIPELINE_ID
      ```
  1. The pipeline should be imported. Run `terraform plan` to see the difference and update the resource accordingly if you don't want to make the change.