# Jobs

Three categories of jobs run on https://ci.bazel.build:

*   bootstrap/maintenance jobs (e.g. bazel-bootstrap)
*   projects (e.g. TensorFlow)
*   hidden jobs

## Bootstrap and maintenance

Several jobs control the bootstrap and maintenance of Bazel, they
are mostly under the `maintenance` and `bazel` folders:

*   `maintenance/install-bazel`: installs Bazel release on all workers
*   `maintenance/gerrit-verifier`: detects pending reviews on Gerrit that
    need validation.

    A review needs validation if somebody marks it as `Presubmit-Ready`.

*   `bazel/nightly`: handles the [Global tests](docs/bazel-monitoring.md#global-tests)

    This job runs every night.

*   `bazel/release`: copy of `bazel/nightly` that runs for the release

    This job also handles publishing the release artifacts.

*   `bazel/presubmit`: copy of `bazel/nightly` that is triggered when someone
     sets `Presubmit-Ready+2` on Gerrit

## Projects

These jobs simply run Bazel on a GitHub repository.

The job templates and definitions are under `//jenkins`.

Particularly interesting is `//jenkins/jobs/jobs.bzl`: it contains the logic
that computes which jobs to run on the prod CI and on the staging CI.

On the staging CI we run fewer jobs than on the prod one, to make full builds
faster.

## Hidden jobs

These jobs are copies of the jobs for the corresponding `<project>`. These jobs
all use the latest Bazel release:

*   `PR/<project>`: validates a GitHub pull request on `<project>`

*   `CR/<project>`: validates a Gerrit review request on `<project>`

*   `Global/<project>`: runs a global presubmit test for changes on `<project>`
