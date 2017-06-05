# Bazel continuous integration for project owners

## Adding a project

To add a project to Bazel CI that is on the `bazelbuild` organization
on GitHub, add a `bazel_github_job` in the `jenkins/jobs/BUILD`
file and send a code review to a CI admin (see
`jenkins/config.bzl`). In the permission of your GitHub repository, you
want to add the team [`robots`](https://github.com/orgs/bazelbuild/teams/robot)
(or [`bazel-io`](https://github.com/bazel-io) for repository outside of
the `bazelbuild` organization) to have write access to the repository.

By default, if the project is in the bazelbuild org and does not need
special tweaks you should add the project to the comprehension
list in the BUILD file. Otherwise you can add a `bazel_github_job` that
takes the following parameters:

* `name` is the name of the job as it will appear in Jenkins.
* `branch` is the branch to build and test, `master` by default.
* `project` is the name of the project, by default it is set to the
  value of `name`. Usefull when renaming a project but keeping the job
  history.
* `org` is the name of the organization on github.
*  `git_url` is the URL to the git repository, default to `https://github.com/<org>/<project>`.
* `project_url` is the URL to the project, default to the value of `git_url`.
* `workspace` is the directory where the workspace is relative to the
  root of the git repository, by default `.`
* `config` can be used to specify a different default configuration
  file. By default it is `//jenkins/build_defs:default.json`. Normally,
  it is no longer needed since the configuration can be changed using a
  file in the repository (see next section).
* `enable_trigger` enable postsubmit test (enabled by default).
* `gerrit_project` specifies a project on the
  [Bazel Gerrit server](https://bazel-review.googlesource.com) that
  mirrors the GitHub project and will be used to trigger presubmit from
  Gerrit.
* `enabled` is used to deactivate a project, `True` by default.
* `pr_enabled` can be set to `False` to turn off presubmit from Pull Requests.
* `run_sequential` can be used to make the job non concurrent, meaning
  that each configuration will run in sequence from the other
  one. Useful if the job use some exclusive resource like [Sauce
  Labs](https://wiki.saucelabs.com/).
* `sauce_enabled` activate [Sauce Labs](https://wiki.saucelabs.com/) support.

A variation of `bazel_github_job`, `bazel_git_job` can be used to
specify a job that runs from a random Git repository instead of a
GitHub repository. It supports the same non GitHub specific argument
but need either `git_url` or `project_url` to be specified.

## Customizing a project

By default, the CI system tries to build `//...` then tests `//...` on Darwin and Linuxes.
To change how the project must be built, a JSON description file can be added to the
repository under `.ci/<name>.json` or `scripts/ci/<name>.json` (where `<name>` is
the name of the project declared in `jobs.bzl`).

This file contains a list of configurations to build and test, each
configuration is a dictionary containing platform description (as
key-value pairs, e.g. `node: "windows-x86\_64"`), a list of parameters
under the key `parameters` and a list of sub-configurations under the
key `configurations`.

A simple configuration with one platform would then look like:

```javascript
[
    {"node": "linux-x86_64"}
]
```

This configuration would build and test on a node that has the label
`linux-x86\_64` with the default set of parameters (i.e. build `//...`
then tests `//...`). To change the target to build and test, this can
be set through `parameters`:

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

This example used `targets` and `tests` parameters to set the targets
to respectively build and tests.

Adding a platform can be done by simply adding another configuration:

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
    }
]
```

But that's a lot of duplication, so we can use sub-configurations instead:

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

Each child configuration inherits parent configuration description. The
child configurations get factored with the parent configuration to create N
configurations that inherit the parameters and descriptor of the parent
configuration. If a child configuration specifies a value already present in the
parent configuration, the parent configuration value will be ignored and the child
configuration value will be used.

For example:

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

would expand to the following configurations:

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

### Configuration descriptor keys

Descriptor keys that have special meaning:

* `node` is a label that describe the platform to run on, e.g.:
  `linux-x86_64`, `windows-x86_64`, `freebsd-11`, ... The complete
  list of currently connected nodes is available on
  http://ci.bazel.io/computer/ and each nodes can be selected either
  by name or by label (to see list of labels of a specific node, click
  on it on the Jenkins UI).
* `variation` is a variation of the Bazel binary, e.g. `-jdk7`.

More descriptor keys can be used to specify more
configuration combination but they won't have any special effects.


### Parameter keys

Possible parameters:

* `configure`: a list of shell (batch on Windows) comnands to execute
  before the build.
* `targets`: the list of targets to build.
* `tests`: the list of targets to test, can be expressed as bazel query expression.
* `build_tag_filters`: list of tags to filter build on.
* `test_tag_filters`: list of tags to filter test on (`-noci,-manual`
  are automatically added).
* `build_opts`: list of options to add to the bazelrc as `build`
 options, note that they impact testing too.
* `test_opts`: list of options to add to the bazelrc as `test` options.


## Bazel bootstrap

__For Bazel developers.__

The Bazel project itself has a separate configuration file for
creating release artifacts. It is stored under
`scripts/ci/bootstrap.json`.

This file follows the same syntax but accepts different parameters:

* `archive`: list of files to archive as a map of target, new name. `%{release_name}` string will
  be replaced by the release name. An empty list means we do not
  archive anything (for non release build).
* `stash`: list of artifacts to stash (to be released / push but no need to keep it forever)
* `targets`: list of targets to build, in addition to //src:bazel.
