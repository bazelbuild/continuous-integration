# Bazel CI workflow

**Note:** the first bazel build is going to stall for some time while
building the base images on docker without any output due to
[bazelbuild/bazel#1289](https://github.com/bazelbuild/bazel/issues/1289).

## Prerequisites

Docker:

*   [At least
    25GB](https://github.com/bazelbuild/continuous-integration/issues/73) of
    free disk space.
*   Your username in the "docker" group.

    Follow the instructions on [Ask
    Ubuntu](https://askubuntu.com/a/477554/671928).

Gcloud:

*   You may need to authenticate and set the current project. To do so, run:

    ```
    gcloud auth login
    gcloud set project bazel-public
    ```

## Pushing changes

The typical worflow when modfiying ci.bazel.build is to first test the
change on ci-staging.bazel.build.

The process typically looks like:

1.  Make your change
2.  Add a few jobs to test to [`jenkins/jobs/jobs.bzl`](jobs.md).
3.  Start the staging Jenkins instance with [`./gce/vm.sh start staging`](vm.md).
4.  Run `bazel run //gcr:deploy-staging` to deploy the change to
    the staging instance.
5.  Restart the staging Jenkins instance by going to
    https://ci-staging.bazel.build/safeExit .
6.  Run a job by identifying it on [https://ci-staging.bazel.build] and
    clicking on the play button.
7.  If 6 fails, go back to 1, skipping step 3.
8.  Send the change to review.
9.  Shut down the staging Jenkins instance with [`./gce/vm.sh stop staging`](vm.md).
10. Once LGTM, deploy to production with `bazel run //gcr:deploy`.
11. Restart the prod Jenkins instance: https://ci.bazel.build/safeExit

    You need to log in to the Jenkins UI, otherwise you may get a stack trace.
    Log in and try again.

## Setting up local testing

You can run a local Jenkins instance with a Docker executor node, by running:

```
bazel run //jenkins:test [-- -p port]
```

It will spin up a Jenkins instance:

*   without security
*   on port `port` (8080 by default)
*   with one node running Ubuntu Wily in Docker

This setup should suffice for local testing.

To stop the instance, go to `http://localhost:8080/safeExit`. This will shut
down Jenkins cleanly.

You can connect additional instance by modifying the UI to test for other
platforms. However this does not enable to test:

*   Synchronization between Gerrit and Github
*   Adding execution nodes
*   Interaction with Github or Gerrit

## Faster testing cycle

If you only need to modify Groovy code under `jenkins/lib`, you can update that
in the running container without restarting Jenkins.

### If you test with a local container

1.  start the container

    ```
    bazel run //jenkins:test
    ```

2.  make your changes to `.groovy` files
3.  transfor the `lib` folder to the running container:

    ```
    jenkins/transfer-lib.sh
    ```

### If you test with the staging Jenkins instance

1.  start the instance

    ```
    gce/vm.sh start staging
    ```

2.  make your changes to `.groovy` files
3.  transfor the `lib` folder to the container running on the staging instance

    ```
    jenkins/transfer-lib-to-staging.sh
    ```

4.  stop the instance when done

    ```
    gce/vm.sh stop staging
    ```
