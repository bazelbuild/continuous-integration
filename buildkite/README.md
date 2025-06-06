# Bazel Continuous Integration

tl;dr:
- _**Want to test your project on Bazel CI? Simply file a request via [this link](https://github.com/bazelbuild/continuous-integration/issues/new?template=adding-your-project-to-bazel-ci.md&title=Request+to+add+new+project+[PROJECT_NAME]&labels=new-project)!**_
- _**Want to see the CI results? Check out the dashboard here: https://buildkite.com/bazel**_

Bazel uses [Buildkite] for continuous integration. The user interface and the orchestration of CI
builds is fully managed by Buildkite, but Bazel brings its own CI machines. The [buildkite folder]
contains all the scripts and configuration files necessary to setup Bazel's CI on Buildkite.

## Reporting a Vulnerability

To report a security issue, please email security@bazel.build with a description
of the issue, the steps you took to create the issue, affected versions, and, if
known, mitigations for the issue. Our vulnerability management team will respond
within 3 working days of your email. If the issue is confirmed as a
vulnerability, we will open a Security Advisory. This project follows a 90 day
disclosure timeline.

## Bazel on Buildkite 101

When you first log into [Buildkite] you are presented with a list of pipelines. A pipeline is a
template of steps that are executed either in sequence or in parallel and that all need to succeed in
order for the pipeline to succeed. The Bazel organisation has dozens of pipelines. Here are a selected
few:

![pipelines]

* The *bazel postsubmit* pipeline builds and tests each commit to Bazel's repository on all supported
platforms.
* The *bazel presubmit* pipeline is triggered on every pull request to Bazel.
* The *rules_go postsubmit* pipeline is triggered on every commit to the [rules_go] repository.
* The *TensorFlow* pipeline builds and tests TensorFlow at `HEAD` every four hours.

### Builds

When you click on a pipeline you can see the last few builds of this pipeline. Clicking on a build
then gives you access to the details of the build. For example, the below image shows a failed build
step on Ubuntu 16.04.

![failed build step]

One can see which tests failed by clicking on the *Test* section. In the below example, the
`//src/test/shell/bazel:external_path_test` was flaky as it failed in 1 out of 5 runs.

![flaky test]

You can view the failed test attempt's `test.log` file in the *Artifacts* tab.

![flaky test log]

### Useful Links

![buildkite useful buttons]

![buildkite testlog buttons]

## Pull Requests

Bazel accepts contributions via pull requests. Contributions by members of the [bazelbuild]
organisation as well as members of individual repositories (i.e. rule maintainers) are whitelisted
automatically and will immediately be built and tested on [Buildkite].

An external contribution, however, first needs to be verified by a project member and therefore will
display a pending status named *Verify Pull Request*.

![status verify pull request]

A member can verify a pull request by clicking on *Details*, followed by *Verify Pull Request*.

![buildkite verify pull request]

*Please vet external contributions carefully as they can execute arbitrary code on our CI machines*

### Build and Test Results

After a pull request has been built and tested, the results will be displayed as a status message on
the pull request. A detailed view is available when clicking on the corresponding *Details*
link. Click [here](https://source.cloud.google.com/results/invocations/dc0510c0-afc6-42b3-8d2e-6d879dec526a/targets)
for an example.

![pull request details]

## Configuring a Pipeline

Each pipeline is configured via a Yaml file. This file either lives in `$PROJECT_DIR/.bazelci/presubmit.yml` (for presubmits) or in an arbitrary location whose path or URL is passed to the CI script (as configured in the Buildkite settings of the respective pipeline). Projects should store the postsubmit configuration in their own repository, but we keep some configurations for downstream projects in https://github.com/bazelbuild/continuous-integration/tree/master/buildkite/pipelines.

### Basic Syntax

The most important piece of the configuration file is the `tasks` dictionary. Each task has a unique key, a platform and usually some build and/or test targets:

```yaml
---
tasks:
  ubuntu_build_only:
    platform: ubuntu2004
    build_targets:
    - "..."
  windows:
    platform: windows
    build_targets:
    - "..."
    test_targets:
    - "..."
```

If there is exactly one task per platform, you can omit the `platform` field and use its value as task ID instead. The following code snippet is equivalent to the previous one:

```yaml
---
tasks:
  ubuntu2004:
    build_targets:
    - "..."
  windows:
    build_targets:
    - "..."
    test_targets:
    - "..."
```

The full list of supported platforms can be found in the PLATFORMS variable in [bazelci.py](./bazelci.py).

### Setting Environment Variables

You can set environment variables for each individual task via the `environment` field:

```yaml
---
tasks:
  ubuntu1804:
    environment:
      CC: clang
    build_targets:
    - "..."
```

### Running Commands, Shell Scripts or Binary Targets

The presubmit configuration allows you to specify a list of shell commands that are executed at the beginning of every job.
Simply add the `batch_commands` (Windows) or `shell_commands` field (all other platforms).

You can even run executable targets via the `run_targets` field.
The following example demonstrates all of these features:

```yaml
---
tasks:
  ubuntu1804:
    shell_commands:
    - rm -f obsolete_file
    run_targets:
    - "//whatever"
    build_targets:
    - "..."
  windows:
    batch_commands:
    - powershell -Command "..."
    build_targets:
    - "..."
```

### Running Bazel coverage

The `coverage_targets` field allows you to specify a list of targets that will be run using `bazel coverage`:

```yaml
---
tasks:
  ubuntu2004:
    coverage_targets:
    - "..."
```

### Using Specific Build & Test Flags

The `build_flags` and `test_flags` fields contain lists of flags that should be used when building or testing (respectively):

```yaml
---
tasks:
  ubuntu1804:
    build_flags:
    - "--define=ij_product=clion-latest"
    build_targets:
    - "..."
    test_flags:
    - "--define=ij_product=clion-latest"
    test_targets:
    - ":clwb_tests"
```

### Sharing Configuration Between Tasks

You can define common configurations and share them between tasks using `*aliases` and the [`<<:` merge key](https://yaml.org/type/merge.html). YAML allows merging maps and sets, but not lists; to merge flags or targets, instead of a list, represent them as a map from strings to null:

```yaml
# This is a map from strings to null, not a list, to allow merging into windows.build_flags and windows.test_flags
.common_flags: &common_flags
  ? "--incompatible_disable_starlark_host_transitions"
  ? "--enable_bzlmod"

.common_task_config: &common_task_config
  build_flags: *common_flags
  build_targets:
    - "//..."
  test_flags: *common_flags
  test_targets:
    - "//tests/..."

tasks:
  ubuntu1804:
    <<: *common_task_config
  ubuntu2004:
    <<: *common_task_config
  windows:
    <<: *common_task_config
    # These are maps from strings to null, not lists, to allow merging
    build_flags:
      <<: *common_flags
      ? "--noexperimental_repository_cache_hardlinks"
    test_flags:
      <<: *common_flags
      ? "--noexperimental_repository_cache_hardlinks"
```

Instead of a map from string to null, you could use a set (via `!!set`); however, sets are unordered, which makes them unsuitable for target lists that use the negation operator.

### Specifying a Display Name

Each task may have an optional display name that can include Emojis. This feature is especially useful if you have several tasks that run on the same platform, but use different Bazel binaries.
Simply set the `name` field:

```yaml
---
tasks:
  windows:
    name: "some :emoji:"
    build_targets:
    - "..."
```

### Generating semantic information with Kythe

You can use `kythe_ubuntu2004` platform along with some `index_*` fields to create a task that generate semantic information of your code with [Kythe](https://kythe.io/).

The `index_targets` field contains list of targets that should be indexed.

The `index_targets_query` field contains a query string that is used to generate additional index targets by command `bazel query ${index_targets_query}`. The returned targets will be merged into `index_targets`.

The `index_flags` field contains list of build flags that should be used when indexing.

The `index_upload_policy` field is used to set policy for uploading generated files. Available values are:
  - `Always`: Always upload generated files even build failed.
  - `IfBuildSuccess`: __Default value__. Only upload generated files if build succeed and raise error when build failed.
  - `Never`: Never upload index files and raise error when build failed.

If `index_upload_gcs` is `True`, the generated files will be uploaded to Google Cloud Storage.

```yaml
---
tasks:
  kythe_ubuntu2004:
    index_targets:
    - "..."
    index_targets_query: "kind(\"java_(binary|import|library|plugin|test|proto_library) rule\", ...)"
    index_flags:
    - "--define=kythe_corpus=github.com/bazelbuild/bazel"
    index_upload_policy: "IfBuildSuccess"
    index_upload_gcs: True
```

### Legacy Format

Most existing configuration use the legacy format with a "platforms" dictionary:

```yaml
---
platforms:
  ubuntu1804:
    build_targets:
    - "..."
    test_targets:
    - "..."
```

The new format expects a "tasks" dictionary instead:

```yaml
---
tasks:
  arbitrary_id:
    platform: ubuntu1804
    build_targets:
    - "..."
    test_targets:
    - "..."
```

In this case we can omit the `platform` field since there is a 1:1 mapping between tasks and platforms. Consequently, the format looks almost identical to the old one:

```yaml
---
tasks:
  ubuntu1804:
    build_targets:
    - "..."
    test_targets:
    - "..."
```

The CI script still supports the legacy format, too.

### Using a specific version of Bazel

The CI uses [Bazelisk](https://github.com/bazelbuild/bazelisk) to support older versions of Bazel, too. You can specify a Bazel version for each pipeline (or even for individual platforms) in the pipeline Yaml configuration:

```yaml
---
bazel: 0.20.0
tasks:
  windows:
    build_targets:
    - "..."
  macos:
    build_targets:
    - "..."
  ubuntu1804:
    bazel: 0.18.0
    build_targets:
    - "..."
[...]
```
In this example the jobs on Windows and MacOS would use 0.20.0, whereas the job on Ubuntu would run 0.18.0.

CI supports several magic version values such as `latest`, `last_green` and `last_downstream_green`.
Please see the [Bazelisk documentation](https://github.com/bazelbuild/bazelisk/blob/master/README.md#how-does-bazelisk-know-which-version-to-run) for more details.

### Testing with incompatible flags

Similar to the aforementioned downstream pipeline you can configure individual pipelines to run with
[`bazelisk --migrate`](https://github.com/bazelbuild/bazelisk#other-features). As a result, the pipeline
runs your targets with all incompatible flags that will be flipped in the next major Bazel release and
prints detailed information about which flags need to be migrated.

You can enable this feature by adding the following code to the top of the pipeline steps in Buildkite at https://buildkite.com/bazel/YOUR_PIPELINE_SLUG/settings, **not** in the pipeline configuration yaml file:

```yaml
---
env:
  USE_BAZELISK_MIGRATE: true
```

 If you want your pipeline to fail if at least one flag needs migration, you need to add this code instead:

```yaml
---
env:
  USE_BAZELISK_MIGRATE: FAIL
```

If you want to enable this feature for a single build, but not for the entire pipeline,
you can follow these steps instead:

1. Navigate to your pipeline in Buildkite.
1. Click on the "New Build" button in the top right corner.
1. Expand the pipeline options via a click on "Options".
1. Enter `USE_BAZELISK_MIGRATE=FAIL` into the "Environment Variables" text field.
1. Click on "Create Build".

### macOS: Using a specific version of Xcode

We upgrade the CI machines to the latest version of Xcode shortly after it is released and this
version will then be used as the default Xcode version. If required, you can specify a fixed Xcode
version to test against in your pipeline config.

**Warning**: We might have to run jobs that specify an explicit Xcode version on separate, slower machines, so we really advise you to not use this feature unless necessary.

The general policy is to *not* specify a fixed Xcode version number, so that we can update the
default version more easily and don't have to update every single CI configuration file out there.

However, if you know that you need to test against multiple versions of Xcode or that newer versions
frequently break you, you can use this feature.

```yaml
tasks:
  # Test against the latest released Xcode version.
  macos:
    build_targets:
    - "..."
  # Ensure that we're still supporting Xcode 10.1.
  macos_xcode_10_1:
    platform: macos
    xcode_version: "10.1"
    build_targets:
    - "..."
```

Take care to quote the version number, otherwise YAML will interpret it as a floating point number.

### Running Buildifier on CI

For each pipeline you can enable [Buildifier](https://github.com/bazelbuild/buildtools/tree/master/buildifier) to check all WORKSPACE, BUILD, BUILD.bazel and .bzl files for lint warnings and formatting violations. Simply add the following code to the top of the particular pipeline configuration:

```yaml
---
buildifier: latest
[...]
```

As a consequence, every future build for this pipeline will contain an additional "Buildifier" step that runs the latest version of Buildifier both in "lint" and "check" mode.
Alternatively you can specify a particular Buildifier version such as "0.20.0".

There is also a more advanced syntax that allows you to specify which [warnings](https://github.com/bazelbuild/buildtools/blob/master/WARNINGS.md) should be checked in [lint mode](https://github.com/bazelbuild/buildtools/tree/master/buildifier#linter):

```yaml
---
buildifier:
  version: latest
  warnings: "positional-args,duplicated-name"
[...]
```

### Using multiple Workspaces in a single Pipeline

Some projects may contain one or more `WORKSPACE` files in subdirectories, in addition to their top-level `WORKSPACE` file.
All of these workspaces can be tested in a single pipeline by using the `working_directory` task property.
Consider the configuration for a project that contains a second `WORKSPACE` file in the `examples_dir/` directory:

```yaml
---
tasks:
  production_code:
    name: "My Project"
    platform: ubuntu1804
    test_targets:
    - //...
  examples:
    name: Examples
    platform: ubuntu1804
    working_directory: examples_dir
    test_targets:
    - //...
```

### Validating changes to pipeline configuration files

You can set the top-level `validate_config` option to ensure that changes to pipeline configuration files in the `.bazelci` directory will be validated.
With this option, every build for a commit that touches a configuration file will contain an additional validation step for each modified configuration file.

Example usage:

```yaml
---
validate_config: 1
tasks:
  macos:
    build_targets:
    - "..."
```

### Exporting JSON profiles of builds and tests

[Bazel's JSON Profile](https://docs.bazel.build/versions/master/skylark/performance.html#json-profile) is a useful tool to investigate the performance of Bazel. You can configure your pipeline to export these JSON profiles on builds and tests using the `include_json_profile` option.

Example usage:

```yaml
---
tasks:
  ubuntu2004:
    include_json_profile:
    - build
    - test
    build_targets:
    - "..."
    test_targets:
    - "..."
```

When `include_json_profile` is specified with `build`, the builds will be carried out with the extra JSON profile flags. Similarly for `test`. Other values will be ignored.

The exported JSON profiles are available as artifacts after each run.

### Matrix Testing

Similar to Github Actions's [matrix testing support](https://docs.github.com/en/actions/learn-github-actions/workflow-syntax-for-github-actions#jobsjob_idstrategymatrix), you can specify a matrix to create multiple tasks by performing variable substitution in a single task configuration.

Example usage:

```yaml
---
matrix:
  bazel_version: ["4.2.2", "5.0.0"]
  unix_platform: ["rockylinux8", "debian10", "macos", "ubuntu2004"]
  python: ["python2", "python3"]
  unix_compiler: ["gcc", "clang"]
  win_compiler: ["msvc", "clang"]

tasks:
  unix_test:
    name: "Test my project on Unix systems"
    platform: ${{ unix_platform }}
    compiler: ${{ unix_compiler }}
    python: ${{ python }}
    build_targets:
    - "//..."
    test_targets:
    - "//..."
  windows_test:
    name: "Test my project on Windows"
    platform: "windows"
    bazel: ${{ bazel_version }}
    compiler: ${{ win_compiler }}
    python: ${{ python }}
    build_targets:
    - "//..."
    test_targets:
    - "//..."
```

The `unix_test` task configuration will generate 16 tasks (4 * 2 * 2) for each `unix_platform`, `unix_compiler`, and `python` combination.

The `windows_test` task configuration will generate 8 tasks (2 * 2 * 2) for each `bazel_version`, `win_compiler` and `python` combination.

## Downstream testing

For existing projects on Bazel CI, you can add your project to [Bazel's downstream testing pipeline](../docs/downstream-testing.md) to catch breakages from Bazel@HEAD as soon as possible.

## FAQ

### My tests fail on Bazel CI due to "Error downloading"

**Q:** I added or changed an external repository and now my test is failing on Bazel CI only with errors like this:

```
WARNING: Download from https://github.com/bazelbuild/java_tools/releases/download/javac11-v11.0/java_tools_javac11_linux-v11.0.zip failed: class java.net.ConnectException Operation not permitted (connect failed)
ERROR: An error occurred during the fetch of repository 'remote_java_tools_linux_beta':
   java.io.IOException: Error downloading [https://github.com/bazelbuild/java_tools/releases/download/javac11-v11.0/java_tools_javac11_linux-v11.0.zip] to /private/var/tmp/_bazel_buildkite/c3a616e1648c5e14a8ab09d0d59696c2/sandbox/darwin-sandbox/3279/execroot/io_bazel/_tmp/58d272c7f3dd803b2bcb2fc7be47d391/root/fb8b458bcc92813a6fcf57a0dbe6e8bd/external/remote_java_tools_linux_beta/java_tools_javac11_linux-v11.0.zip: Operation not permitted (connect failed)
```

**A:** We run most tests on CI without network access and instead inject the external repositories from the outside. This saves a lot of network traffic and I/O (because the Bazel integration tests don't have to extract the repository archives again and again).

In the code review of this PR, philwo@ explained how to fix test failures like this: https://github.com/bazelbuild/bazel/pull/11436.

[Buildkite]: https://buildkite.com
[buildkite folder]: https://github.com/bazelbuild/continuous-integration/tree/master/buildkite
[rules_go]: https://github.com/bazelbuild/rules_go
[Bazel]: https://github.com/bazelbuild/bazel
[bazelbuild]: https://github.com/bazelbuild/

[pipelines]: https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/docs/assets/pipelines.png
[failed build step]: https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/docs/assets/failed-build-step.png
[flaky test]: https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/docs/assets/flaky-test.png
[flaky test log]: https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/docs/assets/flaky-test-log.png
[status verify pull request]: https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/docs/assets/status-verify-pull-request.png
[buildkite verify pull request]: https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/docs/assets/buildkite-verify-pull-request.png
[pull request details]: https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/docs/assets/pull-request-details.png
[buildkite useful buttons]: https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/docs/assets/buildkite-useful-buttons.png
[buildkite testlog buttons]: https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/docs/assets/buildkite-testlog-buttons.png
