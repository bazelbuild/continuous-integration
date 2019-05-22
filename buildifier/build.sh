#!/bin/bash

set -euxo pipefail

docker build -t buildifier .

docker tag buildifier gcr.io/bazel-public/buildifier
docker push gcr.io/bazel-public/buildifier
