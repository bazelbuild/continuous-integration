#!/bin/bash

set -euxo pipefail

./mvnw clean package

rm -rf target/dependency && mkdir -p target/dependency && (cd target/dependency; jar -xf ../dashboard.jar)

docker build -f Dockerfile -t gcr.io/bazel-public/dashboard target