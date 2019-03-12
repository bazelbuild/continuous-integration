# Testing Local Changes With All Downstream Projects

Bazel's [CI system](https://buildkite.com/bazel/) has a pipeline for building Bazel and then testing all configured downstream projects. This can be found at https://buildkite.com/bazel/bazel-at-head-plus-downstream.

If you don't have access to our BuildKite instance, you can request it by sending a message to [the bazel-dev mailing list](https://groups.google.com/forum/#!forum/bazel-dev).

There is a daily scheduled build on this pipeline with the latest HEAD of the [master Bazel branch](https://github.com/bazelbuild/bazel/tree/master), but frequently it can be useful to run these tests with your own changes before merging a pull request.

In order to run this pipeline, your changes need to be in a branch on the [main Bazel repo](https://github.com/bazelbuild/bazel/), not on a fork or your local copy. Most core Bazel contributors can create branches here, but if you can't, you can always ask for help by sending a message to [the bazel-dev mailing list](https://groups.google.com/forum/#!forum/bazel-dev).

## Creating a branch

In order to create a branch suitable for testing, you need to push the commit(s) with the changes to a new named branch in the main Bazel repository. 

For the following commands, I am assuming that your local repository has the commits at HEAD, and that you can refer to the Github remote as `origin`. You can verify this by running `git remote -v`, and if your version of "git@github.com:bazelbuild/bazel.git" is called something else, you should update the commands accordingly.

### Local Changes

To create the new branch, with your changes at HEAD, run:
```bash
$ BRANCH_SUFFIX=feature-foo
$ git push origin HEAD:${USER}-test-${BRANCH_SUFFIX}
```

This creates a branch named "USER-test-feature-foo", which can be viewed at https://github.com/bazelbuild/bazel/tree/USER-test-feature-foo.

It's best to rebase your changes onto a recent version of the master branch, to make it easiest to [compare the results to the latest nightly run](#checking-the-results).

### From Pull Request

Alternately if you're testing a pull request on behalf of someone else you can pull its commits into a new branch in your local bazel repository and then re-export them to the main repository:

```bash
$ # Run in your local bazel repository, with master close to HEAD
$ PULL_REQUEST_ID=1234 # ID of the pull request on github
$ BRANCH_SUFFIX=feature-foo
$ BRANCH_NAME=${USER}-test-${BRANCH_SUFFIX}
$ git fetch origin pull/${PULL_REQUEST_ID}/head:${BRANCH_NAME}
$ git checkout ${BRANCH_NAME}
# Ensure you have a recent version of bazel as the baseline
$ git merge master
$ git push origin ${BRANCH_NAME}
```

## Starting the tests

After the new branch is created, visit the [Bazel (with downstream projects)](https://buildkite.com/bazel/bazel-with-downstream-projects-bazel/) pipeline. Then follow these steps:

1.  Click the "New Build" button at the top right.
2.  Name your build. This should be meaningful to you, but otherwise is just for display purposes.
3.  Leave the "Commit" as `HEAD`
4.  Under "Branch", add the name of your new branch. Ignore the drop-down, you can type directly into the text field.
5.  Click "Create Build" and wait for everything to finish!


## Checking the results

The tests will take time to run, so please be patient. Once they finish, be sure to compare the results against the most recent run named "Scheduled build" under the master branch on the main [Bazel (with downstream projects)](https://buildkite.com/bazel/bazel-with-downstream-projects-bazel) page. The Green Team tries to keep these tests passing, but sometimes there are regressions that aren't fixed yet, and it's unfortunate to try and debug a failure that turns out not to be caused by your changes.

## Cleanup

Once you've finished the tests, be sure to go back to [the list of Bazel branches](https://github.com/bazelbuild/bazel/branches) and delete your branch. This makes it easier to run your downstream tests next time!
