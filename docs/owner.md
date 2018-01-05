# Bazel continuous integration for project owners

## Adding a project

To add a project to Bazel CI that is on the `bazelbuild` GitHub organization:

1.  Allow write access to your repository:

    *   for [`robots`](https://github.com/orgs/bazelbuild/teams/robot), if your
        repository is part of the `bazelbuild` organization
    *   for [`bazel-io`](https://github.com/bazel-io), if your repository is
        outside of the `bazelbuild` organization

2.  Add the job to the job list.

    If the project is in the `bazelbuild` organization and doesn't need special
    tweaking, you can add it to an existing job list in `jenkins/jobs/BUILD`.

    Otherwise add a `bazel_github_job` or `bazel_git_job` rule to
    `jenkins/jobs/BUILD`:

    *   use `bazel_github_job` for jobs from GitHub repositories
    *   use `bazel_git_job` for jobs from Git repositories

3.  Send a Gerrit code review to a CI admin.

    See `jenkins/config.bzl` for the list of admins.

### `bazel_github_job` parameters

The `bazel_github_job` rule takes the following parameters:

*   `name`: name of the job as it will appear in Jenkins
*   `branch`: Git branch to build and test (default: `master`)
*   `project`: name of the project (default: same as `name`)

    Useful when you rename a job but want to keep its history.

*   `org`: name of the organization on GitHub
*    `git_url`: URL to the Git repository (default:
    `https://github.com/<org>/<project>`)
*   `project_url`: URL to the project (default: same as `git_url`)
*   `workspace`: the directory where the workspace is, relative to the
    root of the Git repository (default: `.`)
*   `config`: specifies a default configuration file (default:
    `jenkins/build_defs:default.json`)

    Normally it is not needed because you can change the configuration using
    a file in the repository (see next section).

*   `enable_trigger`: enable postsubmit test (default: true)
*   `poll`: use polling to trigger postsubmit tests instead of waiting
    for GitHub API to notify (default: true if organization is not
    `bazelbuild`)
*   `gerrit_project`: project on the [Bazel Gerrit
    server](https://bazel-review.googlesource.com) that mirrors the GitHub
    project and will be used to trigger presubmits from Gerrit
*   `enabled`: activates or deactivates the project (default: true)
*   `pr_enabled`: enables or disables presubmit from GitHub Pull Requests
*   `run_sequential`: if enabled, runs the job's configurations
    concurrently; otherwise runs the job's configurations one after the
    other

    Useful if the job uses some exclusive resource such as [Sauce
    Labs](https://wiki.saucelabs.com/).

*   `sauce_enabled`: activates or deactivates [Sauce
    Labs](https://wiki.saucelabs.com/) support

### `bazel_git_job` parameters

The `bazel_git_job` rule takes the same parameters as `bazel_github_job`, but
requires that either `git_url` or `project_url` be specified.

## Customizing a project

By default, the CI system tries to build `//...` then to test `//...` on Darwin
and on Linuxes.

You can use a JSON file to change how the project is built:

*   add `.ci/<name>.json` to the project's repository, or
*   or add `scripts/ci/<name>.json` to the
    https://github.com/bazelbuild/continuous-integration repository

Where `<name>` is the name of the project declared in `jobs.bzl`.

This JSON file contains a list of configurations to build and test.
Each configuration entry specifies:

*   a platform name under the `node` key
*   optionally a list of parameters under the key `parameters`
*   optionally a list of sub-configurations under the key `configurations`

### Example 1

A simple configuration with one platform:

```javascript
[
    {"node": "linux-x86_64"}
]
```

This configuration would build and test on a node that has the label
`linux-x86\_64` with the default set of parameters (i.e. build `//...`
then test `//...`).

### Example 2

Built on the previous example:

```javascript
[
    {
        "node": "linux-x86_64",
        "parameters": {
            "targets": ["//my:target"],
            "tests": ["//my:test"],
        }
    }
]
```

This configuration uses `targets` and `tests` parameters to set the targets
to build (`targets`) and to test (`tests`), instead of the default `//...`.

### Example 3

To add a platform, add another configuration:

```javascript
[
    {
        "node": "linux-x86_64",
        "parameters": {
            "targets": ["//my:target"],
            "tests": ["//my:test"],
        }
    },
    {
        "node": "darwin-x86_64",
        "parameters": {
            "targets": ["//my:target"],
            "tests": ["//my:test"],
        }
    },
    {
        "node": "windows-x86_64",
        "parameters": {
            "targets": ["//my:target"],
            "tests": [
                "//my/other/windows/specific:test",
                "//and/some/other/test:name"
            ],
        }
    }
]
```

### Example 4

Use a sub-configurations to reduce repetitions:

```javascript
[
    {
        "configurations": [
            {"node": "linux-x86_64"},
            {"node": "darwin-x86_64"},
        ],
        "parameters": {
            "targets": ["//my:target"],
            "tests": ["//my:test"],
        }
    }
]
```

### Example 5

You can specify child configurations.

Each child configuration inherits parent configuration description. The
child configurations get factored with the parent configuration to create N
configurations that inherit the parameters and descriptor of the parent
configuration. The child configuration can override inherited parameters.

The following configuration:

```javascript
[
    {
        "descriptor": "yeah",
        "parameters": ["targets": ["//:target1"]],
        "configurations": [
            {
                "descriptor2": "a",
                "parameters": ["tests": ["//:test"]]
            },
            {
                "descriptor2": "b",
                "parameters": ["targets": ["//:target2"], "tests": ["//:test"]]
            }
        ]
    }
]
```

would expand to this:

```javascript
[
    {
        "descriptor": "yeah",
        "descriptor2": "a",
        "parameters":  ["targets": ["//:target1"], "tests": ["//:test"]]
    },
    {
        "descriptor": "yeah",
        "descriptor2": "b",
        "parameters": ["targets": ["//:target2"], "tests": ["//:test"]]
    }
]
```

## Reference

### Configuration `descriptor` keys

`descriptor` keys that have special meaning:

*   `node`: a label that describes the platform to run on

    Example: `linux-x86_64`, `windows-x86_64`, `freebsd-11`, etc.

    The complete list of connected nodes is available on
    https://ci.bazel.build/computer/ . You can select nodes either by name or by
    label. To see the list of labels of a specific node, click on the node in
    the Jenkins UI.

*   `variation`: a variation of the Bazel binary, e.g. `-jdk7`

    If not specified, it is assumed to be empty.

You can use more `descriptor` keys to specify more configuration combinations,
but they won't have any special effects.


### Configuration `parameter` keys

Supported `parameter` keys:

*   `configure`: list of Shell commands (Batch commands on Windows) to execute
    before the build
*   `targets`: list of targets to build.
*   `tests`: the list of targets to test; can be a bazel query expression
*   `build_tag_filters`: `tags` filter for the build step; works the same way as
    [test_suite.tags](https://docs.bazel.build/versions/master/be/general.html#test_suite.tags)
*   `test_tag_filters`: `tags` filter for the build step; always considered to
    contain `["-noci", "-manual"]`; works the same way as
    [test_suite.tags](https://docs.bazel.build/versions/master/be/general.html#test_suite.tags)
*   `build_opts`: list of options to add to the bazelrc as `build` options

    Note that such options also affect testing.

*   `test_opts`: list of options to add to the bazelrc as `test` options
*   `startup_opts`: list of options to add to the bazelrc as `startup` options


### `scripts/ci/bootstrap.json` (Bazel bootstrap configuration)

__For Bazel developers.__

The Bazel project itself has a separate configuration file for
creating release artifacts. It is stored under `scripts/ci/bootstrap.json`.

This file follows the same JSON format as discussed in [Customizing a
project](#customizing-a-project) but accepts different parameters:

*   `archive`: list of files to archive

    This is a map of target name to new name.

    The names may contain the `%{release_name}` placeholder, which will be
    replaced by the release name.

    If this parameter is empty then nothing is archived (useful for non-release
    builds).

*   `stash`: list of artifacts to stash

    These artifacts are either:

    *   to be released, or
    *   to be pushed, but there's no need to keep them forever

*   `configure`: list of Shell commands (Batch commands on Windows) to execute
    before building
*   `targets`: list of targets to build, in addition to `//src:bazel`
