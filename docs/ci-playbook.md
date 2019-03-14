# Bazel CI Playbook

_Status: Work in progress_

This guide describes several maintenance workflows that have to be executed frequently.

## Deploying new CI worker images

Our Linux and Windows CI workers run on GCE instances. The basic update process consists of the following two steps:

1. Run [create_images](https://github.com/bazelbuild/continuous-integration/blob/master/buildkite/create_images.py) to create new VM images. This step starts a temporary VM, configures it as a CI worker, and then saves its image in GCE before destroying the temporary VM. This step does not affect running builds.
1. Run [create_instances](https://github.com/bazelbuild/continuous-integration/blob/master/buildkite/create_instances.py) to deploy instances with the new VM images. This step deletes the existing instances, then reads the [configuration file](https://github.com/bazelbuild/continuous-integration/blob/master/buildkite/instances.yml) to determine how many instances are needed, and finally creates new instances with the new images. As a result, any running builds will be interrupted.

Note: Many changes to the Linux workers don't require these two steps since we run Docker containers on Linux. See below for a description on how to create and deploy new Docker images.

### Prerequesites

All steps require `git` and the [Google Cloud SDK](https://cloud.google.com/sdk/install) to be installed on your machine.

### Windows

You need a machine with a recent version of MacOS and Microsoft Remote Desktop (10) installed.

1. First, create new images.
    1. Clone the continuous-integration repository.
    1. `cd` into the `continuous-integration/buildkite` directory.
    1. Create new images by running `python3.6 create_images.py <platform1> <platform2> <...>`. For Windows, this usually means to include `bk-windows-java8` and `bk-trusted-windows-java8`, whereas the `windows-playground` platform is optional. Hint: You can see a list of available platforms by running the script without any arguments.
    1. The script opens Microsoft Remote Desktop to establish a connection to the VM that is used for building the image. Accept any popups and log into the machine by pasting the password into the password field (the script already copied into the clipboard).
    1. Run the setup script by navigating to `C:`, running `powershell` and then executing `.\ setup.ps1`.
    1. Wait until the script has finished. At one point the VM will be rebooted, so the script has to open the remote connection again. This might take a long time.
    1. Login into the Google Cloud Console and check that the created images are no longer busy. Make sure to select the project that matches the image (e.g. `bazel-public` for `trusted` images, `bazel-untrusted` for "normal" images).
    1. If something fails, you can always run `create_images` again.
1. Deploy CI workers with the newly created image by running `python3.6 create_instances.py --local_config`.

### Linux

Most changes can be rolled out by creating and deploying new Docker images. This step requires that Docker is installed and set up, and you need permissions to access the container registry in our GCP project.

1. Clone the continuous-integration repository.
1. `cd` into the `continuous-integration/buildkite/docker` directory.
1. Run `build.sh`.

If you need to create and deploy new VM images, you can follow these steps:

1. Clone the continuous-integration repository.
1. `cd` into the `continuous-integration/buildkite` directory.
1. Create new images by running `python3.6 create_images.py <platform1> <platform2> <...>`. For Linux, this usually means to include `bk-docker` and `bk-trusted-docker`. Hint: You can see a list of available platforms by running the script without any arguments.
1. Deploy CI workers with the newly created image by running `python3.6 create_instances.py --local_config`.

### MacOS

Unfortunately we have to operate a number of physical Mac machines in our office. Please see go/bazel-ci-playbook if you're in the Google network.

## Deploying a new Bazelisk version

1. Create a [new Bazelisk release](https://github.com/philwo/bazelisk/releases). This step has to be done on a Mac machine (due to [cross-compilation problems](https://github.com/golang/go/issues/22510)), and requires permissions to create a release.
1. To deploy this release on MacOS:
    1. Update the [Bazelisk Homebrew formula](https://github.com/fweikert/homebrew-tap/blob/master/Formula/bazelisk.rb).
    1. SSH into the machines and update them via Homebrew (see internal instructions for more details).
1. To deploy this release on Linux:
    1. Update the [Dockerfile](https://github.com/bazelbuild/continuous-integration/blob/master/buildkite/docker/Dockerfile).
    1. Follow the instructions [here](#linux) to deploy new Docker images.
1. To deploy this release on Windows:
    1. Create and deploy new VM images by following the [instructions](#windows). There is no need to update any files manually since the [setup script](https://github.com/bazelbuild/continuous-integration/blob/master/buildkite/setup-windows.ps1) always fetches the latest version of Bazelisk
