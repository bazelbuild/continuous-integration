#!/bin/bash

set -euxo pipefail

for java in java8 nojava; do
  docker build --target ubuntu1404-java8 -t gcr.io/bazel-public/ubuntu1404:$java .
  docker push gcr.io/bazel-public/ubuntu1404:$java

  docker build --target ubuntu1404-java8 -t gcr.io/bazel-untrusted/ubuntu1404:$java .
  docker push gcr.io/bazel-untrusted/ubuntu1404:$java
done

for java in java8 nojava; do
  docker build --target ubuntu1604-java8 -t gcr.io/bazel-public/ubuntu1604:$java .
  docker push gcr.io/bazel-public/ubuntu1604:$java

  docker build --target ubuntu1604-java8 -t gcr.io/bazel-untrusted/ubuntu1604:$java .
  docker push gcr.io/bazel-untrusted/ubuntu1604:$java
done

for java in java8 java9 java10 java11 nojava; do
  docker build --target ubuntu1804-$java -t gcr.io/bazel-public/ubuntu1804:$java .
  docker push gcr.io/bazel-public/ubuntu1804:$java

  docker build --target ubuntu1804-$java -t gcr.io/bazel-untrusted/ubuntu1804:$java .
  docker push gcr.io/bazel-untrusted/ubuntu1804:$java
done
