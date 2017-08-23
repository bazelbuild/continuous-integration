# Using ci.bazel.io

[Bazel CI](http://ci.bazel.io) tests Bazel and a variety of
open-source project that use Bazel. The projects using Bazel are
also used to validate Bazel changes.

Bazel CI is testing both on presubmit (on a pending change) or on
postsubmit (on the master branch). It also handles the release project
of Bazel and the performance benchmarks.

If you wish to add or modify a configuration for one of the project
tested on Bazel CI, go see the
[project owner documentation](owner.md).

<a name="postsubmit">
## Postsubmit

Every project that runs on Bazel CI is run on postsubmit. It is done
using the GitHub API and handled automatically if
[bazel-io](https://github.com/bazel-io) has write access to the
repository.

The result of a build can be either:

  - Sucesss (job is green).
  - Unstable (job is yellow). Some tests failed. Blue Ocean View<sup>1</sup>
    will show the failing platforms in Pipeline view, and list of failing tests
    in Tests view.
  - Failed (job is red). Compilation failed, or configuration files broken.
    Blue Ocean View<sup>1</sup> will show the build breakage. If it does not
    fall back to the full console log.

<sup>1</sup> Open Blue Ocean view with the button on the left of the job view.

Tips:

  - Tests logs are available under the artifacts list (`<joburl>/artifact`, e.g.
    http://ci.bazel.io/job/bazel-tests/lastCompletedBuild/artifact/).
  - Flaky tests can be analyzed with the Test Results Analyzer (available in
    the normal job view on the side menu) which show history per tests.
  - The "Pipeline Steps" button on the side menu on a job view let you examine
    each step of the Jenkins pipeline one by one. Looking for the enclosing
    workspace or node start step of another step give you access to the
    workspace of that step.

Current limitations:

  - Jenkins Blue Ocean UI has no good way to mark an unstable step so if a
    platform stage fails without clear sub-step failing look for the last shell
    step in the platform stage view.
  - Tests are not ordered by platforms in the test view.

## Presubmit

The Bazel CI is able to run presubmit tests of changes from GitHub and
from Gerrit.

A GitHub pull request is tested when an pull request admin comments
__test this please__  or __retest this please__. This presubmit job is
also automatically triggered when an admin pushes a pull request.

  - Admins for pull request are the people from either the
    [bazelbuild](https://github.com/bazelbuild) organization or the
    [google](https://github.com/google) organization.
  - Jenkins identifies those people as admins whose visibility is
    public. To make someone public, go to [the Bazel organization
    page](https://github.com/orgs/bazelbuild/people) (or the
    [Google organization page](https://github.com/orgs/google/people) respectively),
    look for the person's name, and change their visibility to public.

To vet pull request, [bazel-io](https://github.com/bazel-io) must have
write access to the repository (automatic if in the bazelbuild
organization).

Tests on a Gerrit code review are triggered when someone marks the
code review as `Presubmit-Ready+1`. It will update the review thread
with the link to the test results and mark the code review as
`Verified+1` or `Verified-1` depending on the result of the test. To
retrigger a test, simply reset the `Presubmit-Ready` label.

The output should be read the same way as the output of the [postsubmit](#postsubmit).

<a name="global-tests"/>
## Global tests

In addition to pre- and postsubmit tests for an individual change, the
Bazel CI performs a "global test" which builds Bazel from a branch, and
uses that build of Bazel to run all the other jobs on the Bazel CI.

If it succeed to build Bazel (if it is not red), it produces a report
comparing the global test results of this build of Bazel with the global
test results from the latest release of Bazel.

This report can be found at `http://ci.bazel.io/job/bazel/job/<nightly|release|presubmit>/<buildNumber>/Downstream_projects/`,
for instance for the last nigthly run it will be at
[http://ci.bazel.io/job/bazel/job/nightly/lastBuild/Downstream_projects/](http://ci.bazel.io/job/bazel/job/nightly/lastBuild/Downstream_projects/).

The way to read that report is:

  - Every newly failing jobs are problematic and likely to indicate a
    failure due to a Bazel change. It cause the build to be unstable (yellow).
  - Every already failing jobs means that the job result is no worse, it is
    generally safe to ignore those failure but we should aim at having 0 of
    them to make sure we do not hide problem (a build that breaks because of
    Bazel whereas it was broken before of a project issue).
  - Every passing job can be safely ignored.

## Release process

In addition to testing all the jobs, the global test handles pushing
the artifacts that are created by a release branch to GCS and to the
GitHub release system.

## Performance benchmarks

Performance benchmarks run once a day. This job triggers a run of the
performance tests on each new commit. The performance for each commit
is reported at [perf.bazel.build](https://perf.bazel.build).
