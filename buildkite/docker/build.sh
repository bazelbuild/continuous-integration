#!/bin/bash

set -euxo pipefail

for java in java8; do
  docker build --target ubuntu1404-$java -t gcr.io/bazel-public/ubuntu1404:$java .
  docker build --target ubuntu1404-$java -t gcr.io/bazel-untrusted/ubuntu1404:$java .
done

for java in java8; do
  docker build --target ubuntu1604-$java -t gcr.io/bazel-public/ubuntu1604:$java .
  docker build --target ubuntu1604-$java -t gcr.io/bazel-untrusted/ubuntu1604:$java .
done

for java in java11 nojava; do
  docker build --target ubuntu1804-$java -t gcr.io/bazel-public/ubuntu1804:$java .
  docker build --target ubuntu1804-$java -t gcr.io/bazel-untrusted/ubuntu1804:$java .
done
