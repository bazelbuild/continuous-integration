# Jobs

Three categories of jobs run on ci.bazel.io: bootstrap/maintenance,
projects, and hidden jobs.

## Bootstrap and maintenance

Five jobs control the bootstrap and maintenance of Bazel:

* `Github-Trigger`: A job that is automatically triggered (by a GitHub
 webhook) every time someone or something pushes commits to the GitHub
 master branch, to a GitHub release branch, or to a GitHub release
 tag. This job then triggers the `Global/pipeline` job.
* `Bazel-Benchmark` and `Bazel-Push-Benchmark-Output`: jobs running
  continously to produce benchmarks of Bazel published at [perf.bazel.build](https://perf.bazel.build).
* `Global/pipeline`: a job that handles the global tests as well as the release process
* `install-bazel`: a job that install Bazel release on all the slaves.

All those jobs have custom configuration files that can be found in `jenkins/jobs/*.xml.tpl`.

## Projects

All the other jobs are defined by the `bazel_github_job` template that simply run
Bazel on a github repository. The templates are in `jenkins/*.tpl` and the
definitions in `jenkins/jobs/BUILD` and `jenkins/jobs/jobs.bzl`.

The `JOBS` definition in `jenkins/jobs/jobs.bzl` is the list of jobs actually running on
ci.bazel.io. On the staging, to make the full build faster, we use the `STAGING_JOBS` definition,
which is a strip down version of the `JOBS` definition.

## Hidden jobs

* `CR/gerrit-verifier` is a job to detect pending reviews on Gerrit that
  need validation (that have been marked as `Presubmit-Ready`).
* `PR/_project_` is a copy of the job for _project_ that validates a GitHub pull
  request on _project_ with the latest release of Bazel.
* `CR/_project_` is the same as `PR-_project_` but for validating Gerrit
  review request.
* `Global/_project_` is another copy of the job but for use by the
  global presubmit test.
