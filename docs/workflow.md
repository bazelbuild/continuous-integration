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
2.  Deploy to Google Cloud with `bazel run //gcr:deploy`.
3.  Gracefully restart the Jenkins instance: https://ci.bazel.build/safeExit

    If Jenkins doesn't exit fast enough, ensure that no important jobs are
    running and then: https://ci.bazel.build/exit
