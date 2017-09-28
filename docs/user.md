# Using the Bazel CI

[Bazel CI](http://ci.bazel.io) tests Bazel and a variety of
open-source projects that use Bazel.

We also use the projects using Bazel to validate Bazel changes.

The Bazel CI:

*   runs presubmit tests (on a pending change)
*   runs postsubmit tests (on the master branch)
*   handles the release project of Bazel
*   handles performance benchmarks

If you wish to add or modify a configuration for one of the projects on
Bazel CI, see the [project owner documentation](owner.md).

## Postsubmit <a name="postsubmit"></a>

The CI uses the GitHub API and handles test runs automatically if
[bazel-io](https://github.com/bazel-io) has write access to the repository.

The result of a build can be one of:

*   Success (job is green)
*   Unstable (job is yellow), if some tests failed.

    The Blue Ocean View<sup>1</sup> shows the failing platforms in Pipeline view
    and the list of failing tests in Tests view.

*   Failed (job is red), if compilation failed or configuration files are
    broken.

    The Blue Ocean View<sup>1</sup> shows the build breakage. If it doesn't,
    you should look at the full console log.

<sup>1</sup> The Open Blue Ocean view is a Jenkins UI. There's a link to it on
the default Jenkins UI, on the left side in the Job view.

Tips:

*   Test logs are available under the artifacts list via the URL
    `<joburl>/artifact`.

    Example: http://ci.bazel.io/job/bazel-tests/lastCompletedBuild/artifact/

*   Flaky tests can be analyzed with the Test Results Analyzer

    The analyzer is available in the normal job view on the side menu (the one
    which shows the test's history).

*   The "Pipeline Steps" button on the side menu on a job view lets you examine
    each step of the Jenkins pipeline.

    Looking for the enclosing workspace or node start step of another step gives
    you access to the workspace of that step.

Current limitations:

*   Jenkins Blue Ocean UI has no good way to mark an unstable steps.

    If a platform stage fails without clear sub-step failing, look for the last
    shell step in the platform stage view.

*   Tests are not ordered by platforms in the test view.

## Presubmit

The Bazel CI can run presubmit tests for changes from GitHub and from Gerrit.

### GitHub pull requests

A GitHub pull request is tested when:

*   a pull request admin comments "test this please" or "retest this please"
*   an admin pushes a Pull Request

Pull request admins are the people from:

*   the [bazelbuild](https://github.com/bazelbuild) organization, or
*   the [google](https://github.com/google) organization

Jenkins considers those people to be admins whose visibility is public. To make
someone public:

1.  go to [the Bazel organization
    page](https://github.com/orgs/bazelbuild/people) (or the
    [Google organization page](https://github.com/orgs/google/people)
    respectively)
2.  find the person's name and change their visibility to public

To test pull requests, [bazel-io](https://github.com/bazel-io) needs
write access to the repository. This is always the case if the repository is in
the `bazelbuild` organization, otherwise you may need to grant access.

### Gerrit code reviews

A Gerrit code review is tested when someone marks the code review as
`Presubmit-Ready+1`.

Marking the code review as presubmit ready:

*   automatically adds "Bazel CI" as a reviewer
*   updates the review thread with the link to the test results
*   marks the code review as `Verified+1` or `Verified-1` depending on the
    result of the test

To retrigger a test, simply reset the `Presubmit-Ready` label.

You can read the output the same way as of the [postsubmit](#postsubmit).

## Global tests <a name="global-tests"></a>

The Bazel CI can also do a "global test".

A global test:

1.  builds Bazel from a branch
2.  uses the resulting Bazel binary to run all the other jobs on the Bazel CI
3.  produces a report comparing the global test results of this binary and of
    the latest release of Bazel

This report is at
`http://ci.bazel.io/job/bazel/job/<nightly|release|presubmit>/<buildNumber>/Downstream_projects/`.
For example for the last nigthly run it will be at
http://ci.bazel.io/job/bazel/job/nightly/lastBuild/Downstream_projects/ .

The way to read that report is as follows:

*   Newly failing jobs are problematic.

    They are likely to indicate a failure due to a Bazel change. These make the
    build to be unstable (yellow).

*   Already failing jobs may be fine.

    They mean that the job result is no worse than before. It is usually safe to
    ignore these failure, but we should aim to have none of them, because they
    might hide new regressions.

*   Passing jobs are safe to ignore.

## Release process

In addition to testing all the jobs, the [Global test](#global-tests) handles
pushing artifacts that are created by a release branch to GCS and to the GitHub
release system.

## Performance benchmarks

Performance benchmarks run once a day.

This job runs performance tests for each new commit since the previous
benchmarking run, thus each commit is benchmarked individually.

The job publishes a report for each commit, you can find these at
[perf.bazel.build](https://perf.bazel.build).
