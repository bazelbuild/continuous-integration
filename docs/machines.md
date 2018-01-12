# CI machines

This document describes the architecture and administration of the Bazel CI
(Continuous Integration) machines.

## Architecture

Bazel's CI uses Jenkins.

The Jenkins controller runs in a Docker container on a virtual machine (VM).

The Jenkins controller distributes the work to various nodes:

*   VMs on GCE (e.g. Linux and Windows nodes)
*   Physical machines (e.g Mac nodes)
*   Docker containers (e.g. the deploy node that deploys Bazel releases and the
    Bazel homepage)

The Docker containers run on the Jenkins controller's VM.

## Administration

*   VMs: through the `//gce/vm.sh` script
*   Physical machines: physically or through Chrome Remote Desktop
*   Docker containers: through the `//gce/jenkins.yml` files (Google Container
    Engine pod configurations)

### Virtual machines admininstration

You can administer the VMs using the `//gce/vm.sh` script.

You can apply the script's changes to:

*   individual machines, or
*   all machines

`//gce/vm.sh` script commands:

*   `create` and `delete`: create a machine (unless it already exists) or delete
    it
*   `reimage`: `delete` a machine, then `create` it again
*   `start` and `stop`: start or stop the specified machine(s).
*   `update_metadata`: update the metadata for the VM

    The metadata is what we pass to the `--metadata` flags when we run `gcloud
    instances create` commands. The metadata includes the startup scripts and
    the pod configuration for the Docker containers.

The `//gce/vm.sh` script runs `gcloud` and assumes your default GCE project
is the Bazel CI project.

You can install `gcloud` from https://cloud.google.com/sdk/

To set the default `gcloud` project to "bazel-public", run:

```
gcloud config set project bazel-public
gcloud auth login
```

### Physical machines administration

The physical machines need to be on a network allowed for port 50000.  See the
list of IP ranges provided to the [`init.sh`](init.md) script.

The physical manually need to have a service installed that talks to the Jenkins
controller.  The only kind of physical nodes we use are Mac nodes and we need to
set them up manually (for licensing reasons).

To set up a Mac executor node:

1.  install [Xcode](https://developer.apple.com/xcode/downloads/)
2.  install [JDK 8](https://jdk8.java.net/download.html)
3.  create a "ci" user with "sudo" rights
4.  download the `mac/setup_mac.sh` script and run it as the "ci" user:

    ```
    curl -o setup_mac.sh "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/mac/setup_mac.sh"
    sudo su ci -c "/bin/bash setup_mac.sh <node_name>"
    ```
