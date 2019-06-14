#!/bin/bash

set -euxo pipefail

docker push gcr.io/bazel-public/ubuntu1604:java8
docker push gcr.io/bazel-public/ubuntu1804:java11
docker push gcr.io/bazel-public/ubuntu1804:nojava
