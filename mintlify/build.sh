#!/bin/bash

set -euxo pipefail

docker build -t mintlify .

docker tag mintlify gcr.io/bazel-public/mintlify
docker push gcr.io/bazel-public/mintlify
