#!/bin/bash

set -euxo pipefail

docker build --target ubuntu1404-java8 -t gcr.io/bazel-public/ubuntu1404:java8 .
docker push gcr.io/bazel-public/ubuntu1404:java8

docker build --target ubuntu1604-java8 -t gcr.io/bazel-public/ubuntu1604:java8 .
docker push gcr.io/bazel-public/ubuntu1604:java8

for java in java8 java9 java10 nojava; do
  docker build --target ubuntu1804-$java -t gcr.io/bazel-public/ubuntu1804:$java .
  docker push gcr.io/bazel-public/ubuntu1804:$java
done
