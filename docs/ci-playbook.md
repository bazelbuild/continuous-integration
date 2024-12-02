# Bazel CI Playbook

_Status: Work in progress_

This guide describes several maintenance workflows that have to be executed frequently.

## Deploying new CI worker images

Our **Linux** and **Windows** CI workers run on GCE instances. The basic update process consists of the following two steps and has been **automated** in the bazel-trusted BuildKite org:

1. Run [create_images](https://github.com/bazelbuild/continuous-integration/blob/master/buildkite/create_images.py) to create new VM images. This step starts a temporary VM, configures it as a CI worker, and then saves its image in GCE before destroying the temporary VM. This step does not affect running builds.
1. Run [create_instances](https://github.com/bazelbuild/continuous-integration/blob/master/buildkite/create_instances.py) to deploy instances with the new VM images. This step deletes the existing instances, then reads the [configuration file](https://github.com/bazelbuild/continuous-integration/blob/master/buildkite/instances.yml) to determine how many instances are needed, and finally creates new instances with the new images. As a result, any running builds will be interrupted.

Note: Many changes to the Linux workers don't require these two steps since we run Docker containers on Linux. See below for a description on how to create and deploy new Docker images.

For **macOS**, follow the internal playbook (go/bazel-ci-playbook).

### Windows & Linux

You will need to be a member of the `bazel-trusted` BuildKite org.

1. Submit your change to this repository.
1. Initiate a build on the [Create Windows VM image](https://buildkite.com/bazel-trusted/create-windows-vm-image) or [Create Linux VM image](https://buildkite.com/bazel-trusted/create-linux-vm-image) pipeline.
1. Wait for the first build step to finish. This will create a new Windows VM image.
1. Deploy the new image to the `bazel-testing` org by unblocking the next step.
1. Initiate a new build on the [Bazel](https://buildkite.com/bazel-testing/bazel-bazel) pipeline to test the new image.
1. Push the image to prod by unblocking the next step (eg. `bk-testing-windows` to `bk-windows`).
1. Wait for the VMs to be recreated in the bazel and bazel-trusted orgs and the new image to be deployed.

Note: if anything goes wrong in the new image, you can always revert to the previous image by deleting the new image in the GCP console and re-create the VMs.

### Deploy new Docker images for Linux

Most changes can be rolled out by creating and deploying new Docker images. This step requires that

- You are on a Linux machine (images built on macOS may cause problem).
- Docker is installed and set up.
- You need permissions to access the container registry in our GCP project.

Follow these steps to build and deploy a new Docker image:

1. Clear your local Docker cache via `docker builder prune -a -f`.
1. Clone the continuous-integration repository.
1. `cd` into the `continuous-integration/buildkite/docker` directory.
1. Run `build.sh`.
1. Run `push.sh`.

If you are on the `testing` branch, the new image will be pushed to the `gcr.io/bazel-public/testing` repository. If you are on the `master` branch, the new image will be pushed to the `gcr.io/bazel-public` repository.

## Deploying a new Bazelisk version

1. Create a [new Bazelisk release](https://github.com/bazelbuild/bazelisk/releases). This step has to be done on a Mac machine (due to [cross-compilation problems](https://github.com/golang/go/issues/22510)), and requires permissions to create a release.
1. To deploy this release on MacOS:
    1. Update the [Bazelisk Homebrew formula](https://github.com/fweikert/homebrew-tap/blob/master/Formula/bazelisk.rb).
    1. Update the startup script for macOS VMs to install the latest Bazelisk version.
1. To deploy this release on Linux:
    1. Update the [Dockerfile](https://github.com/bazelbuild/continuous-integration/blob/master/buildkite/docker/Dockerfile).
    1. Follow the above instructions to deploy new Docker images.
1. To deploy this release on Windows:
    1. Create and deploy new VM images by following the above instructions. There is no need to update any files manually since the [setup script](https://github.com/bazelbuild/continuous-integration/blob/master/buildkite/setup-windows.ps1) always fetches the latest version of Bazelisk
