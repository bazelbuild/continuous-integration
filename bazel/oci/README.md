# Update Bazel Docker container for new release

To build and publish docker container for new Bazel LTS release to `gcr.io/bazel-public/bazel`, follow those steps:

### 1. Build the docker container on your local Linux machine

```bash
$ ./build.sh gcr.io/bazel-public/bazel <bazel version>
```

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
