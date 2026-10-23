#!/bin/bash

readonly OCI_REPOSITORY=$1
readonly BAZEL_VERSION=$2
JAVA_VERSION=$3
TAG=$BAZEL_VERSION-$JAVA_VERSION

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

if [ -z "$JAVA_VERSION" ]; then
  JAVA_VERSION="openjdk-8-jdk"
fi

GIT_ROOT=$(git rev-parse --show-toplevel)
readonly GIT_ROOT

if docker buildx version &>/dev/null; then
    buildx="buildx"
fi

docker ${buildx:+"${buildx}"} build \
    --file "${GIT_ROOT}/bazel/oci/Dockerfile" \
    --tag "${OCI_REPOSITORY}:${TAG}" \
    --build-arg BAZEL_VERSION="${BAZEL_VERSION}" --build-arg JAVA_VERSION="${JAVA_VERSION}"\
    "${GIT_ROOT}"
