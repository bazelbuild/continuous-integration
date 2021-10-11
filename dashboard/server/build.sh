#!/bin/bash

set -euxo pipefail

GIT_REV=$(git rev-parse --short HEAD)

./mvnw -Dproject.version=${GIT_REV} clean package

rm -rf target/dependency && mkdir -p target/dependency && (cd target/dependency; jar -xf ../dashboard-${GIT_REV}.jar)

docker build -f Dockerfile -t gcr.io/bazel-public/dashboard/server:$GIT_REV target
