#!/bin/bash

set -euxo pipefail

# Enable use of buildkit for all builds. No extra support in the Dockerfile is required.
# See https://docs.docker.com/develop/develop-images/build_enhancements/ for details.
export DOCKER_BUILDKIT=1

for target in bazelisk buildifier github-release saucelabs; do
    docker build -f base/Dockerfile --target $target -t gcr.io/bazel-public/base:$target .
done

docker build -f ubuntu1604/Dockerfile --target ubuntu1604-java8 -t gcr.io/bazel-public/ubuntu1604:java8 ubuntu1604
docker build -f ubuntu1804/Dockerfile --target ubuntu1804-java11 -t gcr.io/bazel-public/ubuntu1804:java11 ubuntu1804
docker build -f ubuntu1804/Dockerfile --target ubuntu1804-nojava -t gcr.io/bazel-public/ubuntu1804:nojava ubuntu1804
docker build -f debian-unstable/Dockerfile --target debian-unstable-java11 -t gcr.io/bazel-public/debian-unstable:java11 debian-unstable
docker build -f centos7/Dockerfile --target centos7-java8 -t gcr.io/bazel-public/centos7:java8 centos7
docker build -f centos7/Dockerfile --target centos7-releaser -t gcr.io/bazel-public/centos7:releaser centos7
