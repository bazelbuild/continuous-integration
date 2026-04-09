#!/bin/bash

set -euxo pipefail

PREFIX="testing/"
if [[ $(git branch --show-current) == "master" ]]; then
    PREFIX=""
fi

IMAGE_NAME="gcr.io/bazel-public/${PREFIX}mintlify"

docker build -t mintlify .

docker tag mintlify "${IMAGE_NAME}"
docker push "${IMAGE_NAME}"
