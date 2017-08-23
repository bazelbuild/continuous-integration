# Bazel continous integration setup

This workspace contains the setup for the continuous integration
system of Bazel. This setup is based on docker images built by bazel.

## For users of Bazel continuous integration system

If you are a user of the CI system, you might be interested in the
following document:

* [owner](docs/owner.md): explains how to add a job for a repository
  owner.
* [user](docs/user.md): explains how to use the CI system for a Bazel
  contributor.

## For maintainers of Bazel continuous integration system

Make sure you have a Bazel installed with a recent enough version of
it. Also make sure [gcloud](https://cloud.google.com/sdk/) and
[docker](https://www.docker.com) are correctly configured on your
machine. Only docker version 1.10 or later is supported.

More documentation:

* [`init.sh`](docs/init.md): initializes the whole CI platform. This
  may delete VMs and do other irreversible changes, so handle with
  care.
* [`vm.sh`](docs/machines.md): lets you control the machines
  (e.g. start/stop them, create/delete/reimage them), including
  the Jenkins controller and the executor nodes.
* [workflow](docs/workflow.md): explains the CI workflow, and
  how you can test local changes with jenkins-staging
* [jobs](docs/jobs.md): explains what jobs are running on the CI
