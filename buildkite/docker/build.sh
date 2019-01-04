#!/bin/bash

set -euxo pipefail

cd ubuntu1404
docker build --target java8 -t gcr.io/bazel-public/ubuntu1404:java8 .
docker push gcr.io/bazel-public/ubuntu1404:java8

cd ../ubuntu1604
docker build --target java8 -t gcr.io/bazel-public/ubuntu1604:java8 .
docker push gcr.io/bazel-public/ubuntu1604:java8

cd ../ubuntu1804
for java in java8 java9 java10 nojava; do
  docker build --target $java -t gcr.io/bazel-public/ubuntu1804:$java .
  docker push gcr.io/bazel-public/ubuntu1804:$java
done
