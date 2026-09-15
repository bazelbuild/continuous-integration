# Update Bazel Docker container for new release

To build and publish docker container for new Bazel LTS release to `gcr.io/bazel-public/bazel`, follow those steps:
(The build.sh file can be found [here](https://github.com/bazelbuild/continuous-integration/blob/master/bazel/oci/build.sh).)

### 1. Build the docker container on your local Linux machine

```bash
$ ./build.sh gcr.io/bazel-public/bazel <bazel version>
```

Note: this installs the Java 8 JDK on the docker container image. To build an image with a more recent JDK version, 
specify the package name of the JDK to install as the third argument, for instance:

```bash
  $ ./build.sh gcr.io/bazel-public/bazel <bazel version> openjdk-21-jdk
```

This will append the JDK version to the tag of the Bazel container image.

### 2. Push the docker container to `gcr.io/bazel-public/bazel`
```bash
$ docker push gcr.io/bazel-public/bazel:<bazel version>
```

### 3. Update the `latest` tag if necessary
If the new Bazel version is the latest version (not a minor/patch release for previous major LTS version):
```bash
$ docker image list gcr.io/bazel-public/bazel:<bazel version>   # To check the <IMAGE ID>.
$ docker tag <IMAGE ID> gcr.io/bazel-public/bazel:latest
$ docker push gcr.io/bazel-public/bazel:latest
```
