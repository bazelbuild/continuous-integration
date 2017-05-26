# Using ci.bazel.io

[Bazel CI](http://ci.bazel.io) tests Bazel and a variety of
open-source project that use Bazel. The projects using Bazel are
also used to validate Bazel changes.

Bazel CI is testing both on presubmit (on a pending change) or on
postsubmit (on the master branch). It also handles the release project
of Bazel and the performance benchmarks.

## Postsubmit

Every project that runs on Bazel CI is run on postsubmit. It is done
using the GitHub API and handled automatically if
[bazel-io](https://github.com/bazel-io) has write access to the
repository.

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

## Global tests

In addition to pre- and postsubmit tests for an individual change, the
Bazel CI performs a "global test" which builds Bazel from a branch, and
uses that build of Bazel to run all the other jobs on the Bazel CI. It
then produces a report comparing the global test results of this build
of Bazel with the global test results from the latest release of
Bazel.

This report can be found at `http://ci.bazel.io/job/Global/job/pipeline/<buildNumber>/Downstream_projects/`,
for instance for the last run it will be at
[http://ci.bazel.io/job/Global/job/pipeline/lastBuild/Downstream_projects/](http://ci.bazel.io/job/Global/job/pipeline/lastBuild/Downstream_projects/).

## Release process

In addition to testing all the jobs, the global test handles pushing
the artifacts that are created by a release branch to GCS and to the
GitHub release system.

## Performance benchmarks

Performance benchmarks run once a day. This job triggers a run of the
performance tests on each new commit. The performance for each commit
is reported at [perf.bazel.build](https://perf.bazel.build).
