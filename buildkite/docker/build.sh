#!/bin/bash

set -euxo pipefail

#Enable use of buildkit for all builds. No extra support in the docker file is required.
export DOCKER_BUILDKIT=1


docker build --target ubuntu1604-java8 -t gcr.io/bazel-public/ubuntu1604:java8 .
docker build --target ubuntu1804-java11 -t gcr.io/bazel-public/ubuntu1804:java11 .
docker build --target ubuntu1804-nojava -t gcr.io/bazel-public/ubuntu1804:nojava .
