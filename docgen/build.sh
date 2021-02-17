#!/bin/bash

set -euxo pipefail

# gcloud builds submit -t gcr.io/bazel-public/docgen .

docker build -t docgen .
docker tag docgen gcr.io/bazel-public/docgen
docker push gcr.io/bazel-public/docgen
