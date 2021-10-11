#!/bin/bash

set -euxo pipefail

GIT_REV=$(git rev-parse --short HEAD)

docker build -f Dockerfile -t gcr.io/bazel-public/dashboard/client:$GIT_REV .
