#!/bin/bash

set -euxo pipefail

for java in java8; do
  docker push gcr.io/bazel-public/ubuntu1404:$java
  docker push gcr.io/bazel-untrusted/ubuntu1404:$java
done

for java in java8; do
  docker push gcr.io/bazel-public/ubuntu1604:$java
  docker push gcr.io/bazel-untrusted/ubuntu1604:$java
done

for java in java11 nojava; do
  docker push gcr.io/bazel-public/ubuntu1804:$java
  docker push gcr.io/bazel-untrusted/ubuntu1804:$java
done
