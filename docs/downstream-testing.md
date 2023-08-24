# Bazel Downstream Testing

Bazel CI offers a pipeline to test Bazel built at a given commit with a list of configured downstream projects. The pipeline can be viewed at https://buildkite.com/bazel/bazel-at-head-plus-downstream, it is scheduled to run nightly and also be triggered manually. The pipeline enables the following benefits:

- Verify Bazel changes against downstream projects before submitting them.
- Detect Bazel regressions at HEAD so that the Bazel team can address them timely.
- Notify downstream project about upcoming breaking changes.
- Test release candidates before pushing the release.

## Downstream projects setup

The downstream project configurations are located in the [bazelci.py](https://github.com/bazelbuild/continuous-integration/blob/0ba2b0b6a8a929afb83dc9aea9761c09baa7b488/buildkite/bazelci.py#L84) script.

You can configure with the following fields:

- `git_repository`: The git repository of this project.
- `http_config`: The [Bazel CI configuration file](../buildkite/README.md#configuring-a-pipeline) of this project.
- `pipeline_slug`: Each downstream project must have an existing pipeline configuration on Bazel CI, you can find the pipeline slug in the URL of the pipeline in the form of `https://buildkite.com/bazel/<pipeline_slug>`.
- `disabled_reason`: The reason to be temporarily disabled from the downstream pipeline. The value is usually a link to the relevant GitHub issue.

### Last green commit

If a project at HEAD is already broken in its own pipeline (usually tested against the latest Bazel LTS release), it doesn't make sense to test the project at HEAD in the downstream pipeline anymore. Therefore, we record a `last_green_commit` for each downstream project, which is the latest commit that is green in its own pipeline. In the downstream pipeline, we test the project at `last_green_commit` instead of `HEAD`. With this approach, we can avoid any breakage that is solely caused by the project's own changes.

## Downstream project policies

The Bazel team monitors the downstream pipeline status and report issues for breakages. To keep the downstream pipeline green, we depend on timely responses from downstream project maintainers to address breaking breakages at HEAD. Therefore, we have the following policies for downstream projects:

- If a breaking change is introduced at Bazel@HEAD, causing a downstream project to break, we will notify the downstream project by filing an issue.
- The downstream project is expected to respond to the issue within 5 working days. Otherwise, the project is eligible to be temporarily disabled in the downstream pipeline. Note that, even if a pipeline is disabled from the [Bazel@HEAD + downstream](https://buildkite.com/bazel/bazel-at-head-plus-downstream) pipeline, the nightly result can still be checked from the [Bazel@HEAD+ Disabled](https://buildkite.com/bazel/bazel-at-head-plus-disabled) pipeline.
- If a project remains disabled in the downstream pipeline for more than 6 months without any indication of a fix, we will remove the pipeline configuration from Bazel's downstream pipeline.

As of May 2023, some projects' pipeline config files live under [the "pipeline" directory](https://github.com/bazelbuild/continuous-integration/tree/master/pipelines) of this repository, which means the Bazel team is responsible for their setup for now, ideally they should be moved to their corresponding repository or the project should be removed.

## Testing Local Changes With All Downstream Projects

To initiate a build for your local change, you'll need "Build & Read" access to https://buildkite.com/bazel/bazel-at-head-plus-downstream. If you are a core Bazel contributor, you can request the access by filing an issue against https://github.com/bazelbuild/continuous-integration, otherwise please reach out to someone who can have access to initate the downstream testing for your PR (e.g. @meteorcloudy, @fweikert, or @Wyverald).

There is a daily scheduled build on this pipeline with the latest HEAD of the [master Bazel branch](https://github.com/bazelbuild/bazel/tree/master), but frequently it can be useful to run these tests with your own changes before merging a pull request.

In order to run this pipeline, your changes need to be available on the [main Bazel repo](https://github.com/bazelbuild/bazel/) as a branch or a PR. Most core Bazel contributors can create branches here. However, it is recommended that you create and upload a change to a personal fork and submit a Pull Request to Bazel.

### Starting the tests

After the new branch or Pull Request is created, visit the [Bazel (with downstream projects)](https://buildkite.com/bazel/bazel-with-downstream-projects-bazel/) pipeline. Then follow these steps:

1.  Click the "New Build" button at the top right.
1.  Name your build. This should be meaningful to you, but otherwise is just for display purposes. By default, Buildkite will use the first line of the commit message.
1.  Leave the "Commit" as `HEAD`
1.  Under "Branch", add `pull/<pr-number>/head` (e.g. `pull/10007/head` for https://github.com/bazelbuild/bazel/pull/10007). If you're using a named branch, enter that name instead. Ignore the drop-down, you can type directly into the text field.
1.  Click "Create Build" and wait for everything to finish!

### Checking the results

The tests will take time to run, so please be patient. Once they finish, be sure to compare the results against the most recent run named "Scheduled build" under the master branch on the main [Bazel (with downstream projects)](https://buildkite.com/bazel/bazel-with-downstream-projects-bazel) page. The Green Team tries to keep these tests passing, but sometimes there are regressions that aren't fixed yet, and it's unfortunate to try and debug a failure that turns out not to be caused by your changes.

### Cleanup

Once you've finished the tests, be sure to check whether you created a named branch and go back to [the list of Bazel branches](https://github.com/bazelbuild/bazel/branches) to delete your branch. This makes it easier to run your downstream tests next time!

## Culprit Finder

[Bazel downstream projects](https://buildkite.com/bazel/bazel-with-downstream-projects-bazel) is red? Use culprit finder to find out which bazel commit broke it!

First you should check if the project is green with the latest Bazel release. If not, probably it's their commits that broke the CI.

If a project is green with release Bazel but red with Bazel nightly, it means some Bazel commit broke it, then culprit finder can help!

Create "New Build" in the [Culprit Finder](https://buildkite.com/bazel/culprit-finder) project with the following environment variable:

- **PROJECT_NAME** (The project name must exist in DOWNSTREAM_PROJECTS in [bazelci.py](https://github.com/bazelbuild/continuous-integration/blob/master/buildkite/bazelci.py))
- (Optional) **TASK_NAME** (The task name must exist in the project's config file, eg. [macos_latest](https://github.com/bazelbuild/rules_apple/blob/master/.bazelci/presubmit.yml#L3)). For old config syntax where platform name is essentially the task name, you can also set PLATFORM_NAME instead of TASK_NAME. If not set, culprit finder will bisect for all tasks of the specified project.
- (Optional) **TASK_NAME_LIST** A list of **TASK_NAME** separated by `,`. You can set this to bisect for multiple tasks in one build. It will be ignored if **TASK_NAME** is set.
- (Optional) **GOOD_BAZEL_COMMIT** (A full Bazel commit, Bazel built at this commit still works for this project). If not set, culprit finder will use the last green bazel commit in downstream pipeline as the good bazel commit.
- (Optional) **BAD_BAZEL_COMMIT** (A full Bazel commit, Bazel built at this commit fails with this project). If not set, culprit finder will use the lastest Bazel commit as the bad bazel commit.
- (Optional) **NEEDS_CLEAN** (Set **NEEDS_CLEAN** to `true` to run `bazel clean --expunge` before each build, this will help reduce flakiness)
- (Optional) **REPEAT_TIMES** (Set **REPEAT_TIMES** to run the build multiple times to detect flaky build failure, if at least one build fails we consider the commit as bad)


eg.
```
PROJECT_NAME=rules_go
PLATFORM_NAME=ubuntu2004
GOOD_BAZEL_COMMIT=b6ea3b6caa7f379778e74da33d1bd0ff6477f963
BAD_BAZEL_COMMIT=91eb3d207714af0ab1e5812252a0f10f40d6e4a8
```

Note: Bazel commit can only be set to commits after [63453bdbc6b05bd201375ee9e25b35010ae88aab](https://github.com/bazelbuild/bazel/commit/63453bdbc6b05bd201375ee9e25b35010ae88aab), Culprit Finder needs to download Bazel at specific commit, but there is no prebuilt Bazel binaries before this commit.

## Bazel Auto Sheriff

[Bazel Auto Sheriff](https://buildkite.com/bazel/bazel-auto-sheriff-face-with-cowboy-hat) is the pipeline to monitor Bazel CI build status and identify reasons for breakages.

Based on a project's build result in main build (with Bazel@Release) and downstream build (with Bazel@HEAD), the Bazel Auto Sheriff does analyzing by the following principles:

* Main Build: PASSED, Downstream build: PASSED

  Everything is fine.

- Main Build: FAILED, Downstream build: PASSED

  Retry the failed jobs to check if they are flaky
  - If passed, report the failed tasks as flaky.
  - If failed, the project is probably broken by its own change.

- Main Build: PASSED, Downstream build: FAILED

  Retry the failed downstream jobs to check if they are flaky

  - If passed, report the failed tasks as flaky.
  - If failed, use culprit finder to do a bisect for each failed project to detect the culprit.

- Main Build: FAILED, Downstream build: FAILED

  Rebuild the project at last green commit

  - If failed, the build is likely broken by an infrastructure change.
  - If passed, analyze main build and downstream build separately according to the same principles as above.

After the analysis, the pipeline will give a summary of four kinds of breakages:

- Breakages caused by infra change.
- Breakages caused by Bazel change, including the culprits identified.
- Breakages caused by the project itself.
- Flaky builds.

You can check the analysis log for more details.

## Checking incompatible changes status for downstream projects

[Bazelisk + Incompatible flags pipeline](https://buildkite.com/bazel/bazelisk-plus-incompatible-flags)
runs [`bazelisk --migrate`](https://github.com/bazelbuild/bazelisk#other-features) on all downstream projects and reports
a summary of all incompatible flags and migrations statuses of downstream projects.

This pipeline works in the following ways:

- The pipeline tests downstream projects with `Bazel@last_green` by default. But you can override the Bazel version by setting the `USE_BAZEL_VERSION` environment variable (e.g. `USE_BAZEL_VERSION=5.3.0`).
- The pipeline fetches the list of incompatible flags to be tested by parsing [open Bazel Github issues](https://github.com/bazelbuild/bazel/issues?q=is%3Aopen+is%3Aissue+label%3Aincompatible-change+label%3Amigration-ready) with `incompatible-change` and `migration-ready` labels. You can override the list of incompatible flags by setting the `INCOMPATIBLE_FLAGS` environment variable (e.g. `INCOMPATIBLE_FLAGS=--foo,--bar`).

This pipeline shows the following information:

- The list of projects that already fail without any incompatible flags. Those projects are already broken due to other reasons, they need to be fixed in the [Bazel@HEAD + Downstream pipeline](https://buildkite.com/bazel/bazel-at-head-plus-downstream) first.
![already failing projects]
- The list of flags that don't break any passing downstream projects or don't break any projects that're owned/co-owned by the Bazel team.
![passing flags]
- The list of projects that are broken by a specific flag.
![projects need migration per flag]
- The list of projects that needs migration for at least one flag.
![projects need migration]
- Click a specific job to check the log and find out which flags are breaking it.
![flags need migration per job]

[already failing projects]: ../buildkite/docs/assets/already-failing-projects.png
[passing flags]: ../buildkite/docs/assets/passing-flags.png
[flags need migration per job]: ../buildkite/docs/assets/flags-need-migration-per-job.png
[projects need migration per flag]: ../buildkite/docs/assets/projects-need-migration-per-flag.png
[projects need migration]: ../buildkite/docs/assets/projects-need-migration.png
