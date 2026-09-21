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

## BCR Downstream Test

`bcr_downstream.py` is a script used for testing whether new or updated BCR module versions break downstream modules that directly depend on them. It vendors the target module(s) via `bazel vendor`, overrides them in each direct downstream module's workspace via `--override_module`, and selects the top direct dependents ranked by BCR PageRank.

A build can be triggered via the `BCR Downstream Test` pipeline (or on a BCR PR branch) with the following environment variables:

* `TARGET_MODULES`: (Optional) A comma-separated list of target module patterns in `<module_pattern>@<version_pattern>` format (e.g. `rules_cc@0.1.1`, `protobuf@latest`). If omitted, target modules are auto-detected from `git diff main...HEAD`.
* `MAX_DOWNSTREAM_MODULES`: (Optional) Maximum number of direct downstream modules to select based on descending global BCR PageRank score. Default is `10`.
* `EXCLUDE_DEV_DEPS`: (Optional) Set to `1` or `true` to exclude `dev_dependency = True` dependencies when discovering direct downstream modules and computing PageRank. Default is `false`.
* `USE_BAZEL_VERSION`: (Optional) Overrides the Bazel version used to test downstream modules (collapsing the `bazel` matrix dimension to reduce CI load). Default is `latest`. Set to empty string `""` to test all Bazel versions configured in each downstream module's `presubmit.yml`.
* `CI_RESOURCE_PERCENTAGE`: (Optional) Percentage of CI machine resources per queue allocated to the `bcr-downstream-test-queue-*` concurrency group. Default is `10` (10%).
* `SKIP_WAIT_FOR_APPROVAL`: (Optional) Set to `1` to bypass the approval block step when needed.

