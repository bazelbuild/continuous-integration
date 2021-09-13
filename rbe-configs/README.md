This directory contains script used to generate and upload RBE toolchain configs. The configs are generated for most Bazel CI
containers. Check the [manifest](https://storage.googleapis.com/bazel-ci/rbe-configs/manifest.json) for the list of available configs.

[`rbe_configs_gen`](https://github.com/bazelbuild/bazel-toolchains) is used to generate the toolchain configs. It works
by running Bazel inside a container to auto-detect available toolchains in it. The detected toolchains are uploaded to GCP 
under `gs://bazel-ci/rbe-configs`.

## Directory structure

```
.
|
|-- cpp_env     # Contains environment variables to be set when generating C++ toolchain configs.
|
+-- generate.py # The python script used to generate and upload configs.
```

## Generation

To (re)generate configs:

1. Make sure `docker` is installed locally.
2. Install [`rbe_configs_gen`](https://github.com/bazelbuild/bazel-toolchains).
3. Run `./generate.py` to generate configs.
4. Run `./generate.py --upload=all` to upload configs and `manifest.json`.

## FAQ

### Do we have to do it everytime we publish Docker images?

Yes. The container image which RBE uses to run your build is determined at generation time - it's the same container
used to detect the toolchains. The image used to run your remote actions can be found at
.e.g `rbe_default.tar/config/BUILD`:

```
...
    "container-image": "docker://gcr.io/bazel-public/ubuntu1604-bazel-java8@sha256:135cb1647b54893531bf220001b07ac34bd2963a59af69659257cc1f121c9958",
...
```

### How do we handle new Bazel release?

Since Bazel 4.0.0+, every release should has corresponding generated configs. For a new release, add the version number to
the script and re-generate the configs.
