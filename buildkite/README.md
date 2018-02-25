# Bazel Continuous Integration

Bazel uses [Buildkite] for continuous integration. The [buildkite folder] contains all the scripts
and configuration files necessary to setup Bazel's CI on Buildkite.

## Bazel on Buildkite 101

[Buildkite] currently does not support anonymous viewing of build results (it's in the works) and
for now requires one to be logged in before being able to trigger builds, view build and test results.
We have set up a separate mechanism to view build and test results for [pull requests](#pull-requests)
and so as a contributor to Bazel you typically don't need access to Buildkite. However, if you are a
maintainer of a repository under the @bazelbuild organisation or a Bazel team member with sheriff
duties you probably do need access, and if so please ping either @buchgr, @philwo or @fweikert and we
will get you on Buildkite.

When you first log into [Buildkite] you are presented with a list of pipelines. A pipeline consists
of steps that are executed either in sequence or in parallel and that all need to succeed in order
for the pipeline to succeed. The Bazel organisation has dozens of pipelines. Here are a selected
few:

![pipelines]

* The *bazel postsubmit* pipeline builds and tests each commit to Bazel's repository on all supported
platforms.
* The *bazel presubmit* pipeline is triggered on every pull request to Bazel.
* The *rules_go postsubmit* pipeline is triggered on every commit to the [rules_go] repository.
* The *TensorFlow* pipeline builds and tests TensorFlow at `HEAD` every four hours.




![failed build step]

![flaky test]

![flaky test log]

## Pull Requests

Bazel accepts contributions via pull requests. Contributions by members of the [bazelbuild]
organisation as well as members of individual repositories (i.e. rule maintainers) are automatically
whitelisted and will be build and tested on [Buildkite] automatically.

An external contribution first needs to be verified by a project member and these contributions
will display a pending status named *Verify Pull Request*.

![status verify pull request]

A member can verify the pull request by clicking on *Details*, followed by *Verify Pull Request*

![buildkite verify pull request]

*Please vet those contributions carefully as they can run arbitrary code on our CI machines.*

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