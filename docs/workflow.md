# Workflow

**Note:** the first bazel build is going to stall for some time while
building the base images on docker without any output due to
[bazelbuild/bazel#1289](https://github.com/bazelbuild/bazel/issues/1289).

The classical worflow when modfiying ci.bazel.io is to first test the
change on ci-staging.bazel.io, so a complete cycle would looks like:

1. Do a change
2. Eventually, add a few jobs to test to
   [`jenkins/jobs/jobs.bzl`](jobs.md).
3. Start the staging instance with
   [`./gce/vm.sh start staging`](vm.md).
4. Run `bazel run //gcr:deploy-staging` to deploy the change to
   the staging instance.
5. Restart the staging jenkins instance by going to
   [http://ci-staging.bazel.io/safeExit](http://ci-staging.bazel.io/safeExit).
6. Run a job by identifying on [http://ci-staging.bazel.io] and
   clicking on the play button.
7. If 6 fails, go back to 1, skipping step 3.
8. Send the change to review, reverting the change in 3.
9. Once LGTM, deploy to production with `bazel run //gcr:deploy`.
10. Finally, restart the prod jenkins instance by going to
   [http://ci.bazel.io/safeExit](http://ci.bazel.io/safeExit).

## Setting up for local testing

There is a way to run a local jenkins instance with a docker executor node,
by running

```
bazel run //jenkins:test [-- -p port]
```

It will setup a Jenkins instance without security on port `port`
(8080 by default) and one node running Ubuntu Wily in Docker. This
should be enough for local testing. To stop the instance, goes to
`http://localhost:8080/safeExit` and this will shutdown cleanly.

You can connect additional instance by modifying the UI to test
for other platforms. This does not enable to test:

  - Synchronization between Gerrit and Github,
  - Adding execution nodes,
  - Interaction with Github or Gerrit.
