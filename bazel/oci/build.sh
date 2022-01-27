#!/bin/bash

readonly OCI_REPOSITORY=$1
readonly BAZEL_VERSION=$2

set -o errexit -o nounset -o pipefail

function print_usage() {
    >&2 echo "Usage: $0 <OCI_REPOSITORY> <BAZEL_VERSION>"
}

if [ -z "${OCI_REPOSITORY}" ]; then
    >&2 echo "ERROR: missing 'OCI_REPOSITORY' argument"
    print_usage
    exit 1
fi

if [ -z "${BAZEL_VERSION}" ]; then
    >&2 echo "ERROR: missing 'BAZEL_VERSION' argument"
    print_usage
    exit 1
fi

GIT_ROOT=$(git rev-parse --show-toplevel)
readonly GIT_ROOT

if docker buildx version 2>&1 1>/dev/null; then
    buildx="buildx"
fi

docker ${buildx:+"${buildx}"} build \
    --file "${GIT_ROOT}/bazel/oci/Dockerfile" \
    --tag "${OCI_REPOSITORY}:${BAZEL_VERSION}" \
    --build-arg BAZEL_VERSION="${BAZEL_VERSION}" \
    "${GIT_ROOT}"
