#!/bin/bash

set -euxo pipefail

PREFIX="bazel-public"

# Enable use of buildkit for all builds. No extra support in the Dockerfile is required.
# See https://docs.docker.com/develop/develop-images/build_enhancements/ for details.
export DOCKER_BUILDKIT=1

for target in bazelisk github-release; do
    docker build -f base/Dockerfile --target $target -t gcr.io/bazel-public/base:$target .
done

# Containers used by Bazel CI
docker build -f centos7/Dockerfile    --target centos7-java8           -t "gcr.io/$PREFIX/centos7-java8" centos7
docker build -f centos7/Dockerfile    --target centos7-releaser        -t "gcr.io/$PREFIX/centos7-releaser" centos7
