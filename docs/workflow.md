# Bazel CI workflow

## Prerequisites

Docker:

*   [At least
    25GB](https://github.com/bazelbuild/continuous-integration/issues/73) of
    free disk space.

*   Your username in the "docker" group.

    Follow the instructions on [Ask Ubuntu](https://askubuntu.com/a/477554/671928).

Gcloud:

*   You may need to authenticate and set the current project. To do so, run:

    ```
    gcloud auth login
    gcloud config set project bazel-public
    gcloud config set zone europe-west1-d
    ```

## Pushing changes

The process typically looks like:

1.  Make your change.
2.  Deploy to production with `bazel run //gcr:deploy`.
3.  Gracefully restart the Jenkins instance: https://ci.bazel.build/safeExit

    If Jenkins doesn't exit fast enough, ensure that no important jobs are
    running and then: https://ci.bazel.build/exit

## Setting up local testing

You can run a local Jenkins instance with a Docker executor node, by running:

```
bazel run //jenkins/test [-- -p port]
```

It will spin up a Jenkins instance:

*   without security
*   on port `port` (8080 by default)
*   with one node running Ubuntu Wily in Docker

This setup should suffice for local testing.

To stop the instance, go to `http://localhost:8080/exit`. This will shut
down Jenkins cleanly.

You can connect additional instance by modifying the UI to test for other
platforms. However this does not enable to test:

*   Synchronization between Gerrit and Github
*   Adding execution nodes
*   Interaction with Github or Gerrit

## Faster testing cycle

If you only need to modify Groovy code under `jenkins/lib`, you can update that
in the running container without restarting Jenkins.

1.  Start the container:

    ```
    bazel run //jenkins/test
    ```

2.  Make your changes to `.groovy` files.
3.  Transfer the `lib` folder to the running container:

    ```
    jenkins/transfer-lib.sh
    ```
