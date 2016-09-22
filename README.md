# Bazel continous integration setup

This workspace contains the setup for the continuous integration
system of Bazel. This setup is based on docker images built by bazel.

Make sure you have a Bazel installed with a recent enough version of
it. Also make sure [gcloud](https://cloud.google.com/sdk/) and
[docker](https://www.docker.com) are correctly configured on your
machine.

More documentation:

* [`init.sh`](docs/init.md): initializes the whole CI platform. This
  may delete VMs and do other irreversible changes, so handle with
  care.
* [`vm.sh`](docs/machines.md): lets you control the machines
  (e.g. start/stop them, create/delete/reimage them), including
  the Jenkins master and the Jenkins slaves
* [workflow](docs/workflow.md): explains the CI workflow, and
  how you can test local changes with jenkins-staging
* [jobs](docs/jobs.md): explains what jobs are running on the CI
