#!/bin/bash

set -euxo pipefail

gcloud compute instances delete docker-cache --zone=europe-west1-c --quiet

gcloud compute instances create-with-container \
  --project bazel-public \
  --zone "europe-west1-c" \
  --boot-disk-device-name "docker-cache" \
  --boot-disk-size 250GB \
  --boot-disk-type pd-ssd \
  --container-env "REGISTRY_PROXY_REMOTEURL=https://registry-1.docker.io" \
  --container-image "registry:2" \
  --container-restart-policy always \
  --image-family cos-stable \
  --image-project cos-cloud \
  --machine-type n1-standard-4 \
  --network buildkite \
  --network-tier PREMIUM \
  docker-cache
