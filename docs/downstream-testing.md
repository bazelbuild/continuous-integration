# Testing Local Changes With All Downstream Projects

Bazel's [CI system](https://buildkite.com/bazel/) has a pipeline for building Bazel and then testing all configured downstream projects. This can be found at https://buildkite.com/bazel/bazel-at-head-plus-downstream.

If you don't have access to our BuildKite instance, you can request it by sending a message to [the bazel-dev mailing list](https://groups.google.com/forum/#!forum/bazel-dev).

There is a daily scheduled build on this pipeline with the latest HEAD of the [master Bazel branch](https://github.com/bazelbuild/bazel/tree/master), but frequently it can be useful to run these tests with your own changes before merging a pull request.

In order to run this pipeline, your changes need to be available on the [main Bazel repo](https://github.com/bazelbuild/bazel/), not on a fork or your local copy. Most core Bazel contributors can create branches here. However, it is recommended that you create and upload a change to a personal fork and submit a Pull Request to Bazel.

## Starting the tests

After the new branch or Pull Request is created, visit the [Bazel (with downstream projects)](https://buildkite.com/bazel/bazel-with-downstream-projects-bazel/) pipeline. Then follow these steps:

1.  Click the "New Build" button at the top right.
2.  Name your build. This should be meaningful to you, but otherwise is just for display purposes. By default, Buildkite will use the first line of the commit message.
3.  Leave the "Commit" as `HEAD`
4.  Under "Branch", add `pull/<pr-number>/head` (e.g. `pull/10007/head` for https://github.com/bazelbuild/bazel/pull/10007). If you're using a named branch, enter that name instead. Ignore the drop-down, you can type directly into the text field.
5.  Click "Create Build" and wait for everything to finish!


## Checking the results

The tests will take time to run, so please be patient. Once they finish, be sure to compare the results against the most recent run named "Scheduled build" under the master branch on the main [Bazel (with downstream projects)](https://buildkite.com/bazel/bazel-with-downstream-projects-bazel) page. The Green Team tries to keep these tests passing, but sometimes there are regressions that aren't fixed yet, and it's unfortunate to try and debug a failure that turns out not to be caused by your changes.

## Cleanup

Once you've finished the tests, be sure to check whether you created a named branch and go back to [the list of Bazel branches](https://github.com/bazelbuild/bazel/branches) to delete your branch. This makes it easier to run your downstream tests next time!
