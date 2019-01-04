#!/bin/bash

set -euxo pipefail

cd ubuntu1404
docker build --target java8 -t gcr.io/bazel-public/ubuntu1404:java8

cd ../ubuntu1604
docker build --target java8 -t gcr.io/bazel-public/ubuntu1604:java8

cd ../ubuntu1804
docker build --target java8 -t gcr.io/bazel-public/ubuntu1804:java8
docker build --target nojava -t gcr.io/bazel-public/ubuntu1804:nojava
docker build --target java9 -t gcr.io/bazel-public/ubuntu1804:java9
docker build --target java10 -t gcr.io/bazel-public/ubuntu1804:java10
