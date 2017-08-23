# How to monitor for Bazel regression?

This is a guide on what to monitor for Bazel for the
Bazel build sheriff.

# The dashboard

A general dashboard to have a quick view of the general health is available
at (http://ci.bazel.io/view/Dashboard/)[http://ci.bazel.io/view/Dashboard/].
This dashboard represent the health of all important builds that runs on the CI
system.

There is 2 kinds of projects we monitor:

  - Owned by the core bazel team:
    [bazel-tests](http://ci.bazel.io/job/bazel-tests),
    [bazel-docker-tests](http://ci.bazel.io/job/bazel-docker-tests),
    [Tutorial](http://ci.bazel.io/job/Tutorial),
    [benchmark](http://ci.bazel.io/job/benchmark),
    [nightly](http://ci.bazel.io/job/bazel/job/nightly) and
    [release](http://ci.bazel.io/job/bazel/job/release)
  - Projects built using Bazel such as repositories on the bazelbuild GitHub
    organisation, TensorFlow or Gerrit.

If project owned by the Bazel team are not green, then the Bazel team needs to
investigate and fix as soon as possible to keep our build green.

The other projects health depends on the other projects owner and the Bazel team
responsibility is only to report issue and if the build stay broken for too
long (more than a week), to deactivate the project. Those projects are useful
for the Bazel team to test non regression in Bazel itself.

# Triaging failure

The build sheriff should monitor the output of the various type of job:

  - [Global tests](user.md#global-jobs) (e.g.
    [nightly](http://ci.bazel.io/job/bazel/job/nightly) and
    [release](http://ci.bazel.io/job/bazel/job/release)).
    The [release](http://ci.bazel.io/job/bazel/job/release) job runs at every
    push and is always green for non release push. The
    [nightly](http://ci.bazel.io/job/bazel/job/nightly) job runs every night
    and can be re-run on demand simply using the run button in Jenkins (needs
    to be logged in). See the [user guide](user.md#global-jobs) on how to
    interpret the results. Serious failure in the a global test should be filed
    to [bazelbuild/bazel](https://github.com/bazelbuild/bazel/issues/new) as
    a breakage, and as release blocker if on the release job.
  - [benchmark](http://ci.bazel.io/job/benchmark) should be investigated
    just by looking at the output logs. If the job fails with a java error,
    build error, an issue should be filed to
    [bazelbuild/bazel](https://github.com/bazelbuild/bazel/issues/new), else it
    should be filed to [bazelbuild/continuous-integration](https://github.com/bazelbuild/bazel/continuous-integration/new).
  - [postsubmits](user.md#postsubmit), which are all the other monitored
    jobs. A postsubmit failure should be reported to the project owning the
    job. If a failure stay for too long, the job should be partially or totally
    deactivated to maintain the clarity of global tests.
