# Jobs

Two categories of job run on ci.bazel.io: bootstrap/maintenance and projects.

## Bootstrap and maintenance

3 jobs control the bootstrap and maintenance of Bazel:

* `Github-Trigger`: a control job, launched by a Github webhook, that triggers the `Global/pipeline` job
  if there is push to the master branch, to a release branch or to a release tag.
* `Bazel-Bechmark` and `Bazel-Push-Benchmark-Output`: are job running
  continously to
* `Global/pipeline` handles the global tests as well as the release process

All those jobs have custom configuration files that can be found in `jenkins/jobs/*.xml.tpl`.

## Projects

All the other jobs are defined by the `bazel_github_job` template that simply run
Bazel on a github repository. The templates are in `jenkins/*.tpl` and the
definitions in `jenkins/jobs/BUILD` and `jenkins/jobs/jobs.bzl`.

The `JOBS` definition in `jenkins/jobs/jobs.bzl` is the list of jobs actually running on
ci.bazel.io. On the staging, to make the full build faster, we use the `STAGING_JOBS` definition,
which is a strip down version of the `JOBS` definition.

## Hidden jobs

In addition to those jobs, some more "hidden jobs" exists on the ci:

* `CR/gerrit-verifier` is a custom job to detect pending reviews on gerrit that
  need validation (that have been marked as `Presubmit-Ready`).
* `PR/_project_` is a copy of the job for _project_ that validates a Github Pull
  Request on _project_ with the latest release of Bazel. A pull request
  is validated when an pull request admin comments __test this please__
  or __retest this please__. It also auto-triggers this job when an
  admin pushes a pull request.
  - Admins for pull request are the people from either the
    [bazelbuild](https://github.com/bazelbuild) organization or the
    [google](https://github.com/google) organization.
  - Jenkins identifies those people as admins whose visibility is
    public. To make someone public, go to [the Bazel organization
    page](https://github.com/orgs/bazelbuild/people) (or the
    [Google organization page](https://github.com/orgs/google/people) respectively),
    look for the person's name, and change their visibility to public.
* `CR/_project_` is the same as `PR-_project_` but for validating Gerrit
  review request.
* `Global/_project_` is another copy of the job but for use by the
  global presubmit test.
