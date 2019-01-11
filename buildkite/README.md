# Bazel Continuous Integration

Bazel uses [Buildkite] for continuous integration. The user interface and the orchestration of CI
builds is fully managed by Buildkite, but Bazel brings its own CI machines. The [buildkite folder]
contains all the scripts and configuration files necessary to setup Bazel's CI on Buildkite.

## Bazel on Buildkite 101

[Buildkite] currently does not support public viewing of build and test results (it's actively being
[worked](https://github.com/buildkite/feedback/issues/137#issuecomment-360336774) on)
and for now requires one to be logged in. In the meantime, we have set up a separate mechanism to
view build and test results of [pull requests](#build-and-test-results) and so as a contributor to
Bazel you typically don't need access to Buildkite. However, if you are a maintainer of a repository
under the @bazelbuild organisation or a Bazel team member with sheriffing duties you probably do need
access. Please ping either @buchgr, @philwo or @fweikert if you don't have access to Bazel on Buildkite
but think you should.

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


### Culprit Finder

[Bazel downstream projects](https://buildkite.com/bazel/bazel-with-downstream-projects-bazel) is red? Use culprit finder to find out which bazel commit broke it!

First you should check if the project is green with the latest Bazel release. If not, probably it's their commits that broke the CI.

If a project is green with release Bazel but red with Bazel nightly, it means some Bazel commit broke it, then culprit finder can help!

Create "New Build" in the [Culprit Finder](https://buildkite.com/bazel/culprit-finder) project with the following environment variable:

- PROJECT_NAME (The project name must exists in DOWNSTREAM_PROJECTS in [bazelci.py](https://github.com/bazelbuild/continuous-integration/blob/master/buildkite/bazelci.py))
- PLATFORM_NAME (The platform name must exists in PLATFORMS in [bazelci.py](https://github.com/bazelbuild/continuous-integration/blob/master/buildkite/bazelci.py))
- GOOD_BAZEL_COMMIT (A full Bazel commit, Bazel built at this commit still works for this project)
- BAD_BAZEL_COMMIT (A full Bazel commit, Bazel built at this commit fails with this project)

eg.
```
PROJECT_NAME=rules_go
PLATFORM_NAME=ubuntu1404
GOOD_BAZEL_COMMIT=b6ea3b6caa7f379778e74da33d1bd0ff6477f963
BAD_BAZEL_COMMIT=91eb3d207714af0ab1e5812252a0f10f40d6e4a8
```

Note: Bazel commit can only be set to commits after [63453bdbc6b05bd201375ee9e25b35010ae88aab](https://github.com/bazelbuild/bazel/commit/63453bdbc6b05bd201375ee9e25b35010ae88aab), Culprit Finder needs to download Bazel at specific commit, but we didn't prebuilt Bazel binaries before this commit.

## Running Buildifier on CI

For each pipeline you can enable [Buildifier](https://github.com/bazelbuild/buildtools/tree/master/buildifier) to check whether all BUILD and .bzl files comply with the standard formatting convention. Simply add the following code to the top of the particular pipeline Yaml configuration (either locally in `.bazelci/presubmit.yml` or in https://github.com/bazelbuild/continuous-integration/tree/master/buildkite/pipelines):

```
buildifier: {}
```

As a consequence, every future build for this pipeline will contain an additional "Buildifier" step that runs the latest version of Buildifier on all BUILD and .bzl files in "lint" mode.

### Running a specific version of Buildifier

You can also specify which version of Buildifier should be run:

```
buildifier:
  version: latest
```

The configuration value can be a hardcoded version string such as "0.20.0" or a dynamic reference such as "latest", "latest-1", etc. The latest Buildifier version will be used if the configuration does not contain the "version" field.

### Specifying the set of input files

By default Buildifier only processes BUILD and .bzl files. This can be changed by adding the "files" field to the configuration:

```
buildifier:
  files:
  - "*.bzl"
  - "BUILD.bazel"
  - "BUILD"
```

All values must be valid input for [find(1)](https://linux.die.net/man/1/find).
