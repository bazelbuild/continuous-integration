## BCR Postsubmit

`bcr_postsubmit.py` is a script used for Bazel Central Registry (BCR) postsubmit operations. It synchronizes the `bazel_registry.json` and the `modules/` directory from the main branch of the Bazel Central Registry to the BCR's public cloud storage bucket.

## BCR Presubmit

`bcr_presubmit.py` is a script used for Bazel Central Registry (BCR) [presubmit operations](https://github.com/bazelbuild/bazel-central-registry/blob/main/docs/README.md#presubmit). This script primarily handles the preparation and execution of tests for new modules or updated versions of modules being added to the Bazel Central Registry.

This script powers the [BCR Presubmit](https://buildkite.com/bazel/bcr-presubmit) pipeline, which respects:

* `CI_RESOURCE_PERCENTAGE`: (Optional) Specifies the percentage of CI machine resources to use for running tests. Default is 30%. **ATTENTION**: please do NOT overwhelm CI during busy hours.

## BCR Bazel Compatibility Test

`bcr_compatibility.py` is a script used for testing compatibility between any versions of Bazel and BCR modules, and optionally with given incompatible flags.

A new build can be triggered via the [BCR Bazel Compatibility Test](https://buildkite.com/bazel/bcr-bazel-compatibility-test) pipeline with the following environment variables:

* `MODULE_SELECTIONS`: (Mandatory) A comma-separated list of module patterns to be tested in the format `<module_pattern>@<version_pattern>`. A module is selected if it matches any of the given patterns.

    The `<module_pattern>` can include wildcards (*) to match multiple modules (e.g. `rules_*`).

    The `<version_pattern>` can be:

    - A specific version (e.g. `1.2.3`)
    - `latest` to select the latest version
    - A comparison operator followed by a version (e.g. `>=1.0.0`, `<2.0.0`)

    Examples: `rules_cc@0.0.13,rules_java@latest`, `rules_*@latest`, `protobuf@<29.0-rc1`

* `SELECT_TOP_BCR_MODULES`: (Optional) Set this env var to select the top N most important modules from the BCR for testing (based on their PageRank values). This will override the `MODULE_SELECTIONS` env var.

* `SMOKE_TEST_PERCENTAGE`: (Optional) Specifies a percentage of selected modules to be randomly sampled for smoke testing.

    For example, if `MODULE_SELECTIONS=rules_*@latest` and `SMOKE_TEST_PERCENTAGE=10`, then 10% of modules with name starting with `rules_` will be randomly selected.

* `USE_BAZEL_VERSION`: (Optional) Specifies the Bazel version to be used. The script will override Bazel version for all task configs.

* `USE_BAZELISK_MIGRATE`: (Optional) Set this env var to `1` to enable testing incompatible flags with Bazelisk's [`--migrate`](https://github.com/bazelbuild/bazelisk?tab=readme-ov-file#--migrate) feature. A report will be generated for the pipeline if this feature is enabled.

* `INCOMPATIBLE_FLAGS`: (Optional) Specifies the list of incompatible flags to be tested with Bazelisk. By default incompatible flags are fetched by parsing titles of [open Bazel Github issues](https://github.com/bazelbuild/bazel/issues?q=is%3Aopen+is%3Aissue+label%3Aincompatible-change+label%3Amigration-ready) with `incompatible-change` and `migration-ready` labels. Make sure the Bazel version you select support those flags.

* `CI_RESOURCE_PERCENTAGE`: (Optional) Specifies the percentage of CI machine resources to use for running tests. Default is 30%. **ATTENTION**: please do NOT overwhelm CI during busy hours.
