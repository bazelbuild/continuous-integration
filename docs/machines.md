# Handling machines

# Quick description  of the architecture

Bazel's CI use Jenkins in a docker container to run the various test jobs.
The Jenkins controller distribute this work on various nodes:

* Virtual machines on GCE (Linux and Windows nodes)
* Docker container (the deploy node which is used for deploying
  release and the website)
* Physical machines (mac nodes)

The docker containers are run on the jenkins controller virtual machine, the Jenkins
controller runs in a docker container itself. They are administered through the
`gce/jenkins.yml` and `gce/jenkins-staging.yml` files (a Google Container
Engine pod configuration).

The virtual machines are administered through the `gce/vm.sh` script.

## Virtual machines admininstration

Commands from the `gce/vm.sh` script can be applied to all machines,
individual machines or all machines from `staging` or `prod`:

* `create` and `delete`: create a machine (unless it already exists) or delete it.
* `reimage`: `delete` a machine, then `create` it again.
* `start` and `stop`: start or stop the specified VMs, classically used to shut down the
    staging instance.
* `update_metadata`: update the metadata for the VM. It is the data
    that we pass to the `--metadata` flags when we do `gcloud
    instances create`  which includes the startup scripts and
    the pod configuration for the docker containers.

This script needs access to `gcloud` and assumes your default GCE project is pointing to the
CI project. You can install `gcloud` from https://cloud.google.com/sdk/ and set it
up so the default project is "bazel-public".

```
$ gcloud config set project bazel-public
$ gcloud auth login
```

## Physical machines administration

The physical machines needs to be in a network allowed for port 50000, see the list of IP
ranges provided to the [`init.sh`](init.md) script.

They need to have installed a service that talks to the Jenkins controller.  The only kind of
physical nodes we currently use are Mac nodes. For licensing reasons, those nodes
have to be set up manually.

### Setting up a Mac executor node

1. Install [Xcode](https://developer.apple.com/xcode/downloads/)
  and [JDK 8](https://jdk8.java.net/download.html)
2. Create a "ci" user with "sudo" right, download the
  `mac/setup_mac.sh` script, and run it as that user:
```
$ curl -o setup_mac.sh "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/mac/setup_mac.sh"
$ sudo su ci -c "/bin/bash setup_mac.sh <node_name>"
```
