#!/bin/bash

set -euxo pipefail
PREFIX=bazel-public
GIT_ROOT="$(git rev-parse --show-toplevel)"
source "$GIT_ROOT/buildkite/docker/utils.sh"
DEFAULT_IMAGE_TAG="$(calculate_image_tag)"
export IMAGE_TAG="${IMAGE_TAG:-$DEFAULT_IMAGE_TAG}"

# Containers used by Bazel CI
docker push "gcr.io/$PREFIX/rockylinux8" &
docker push "gcr.io/$PREFIX/rockylinux8:$IMAGE_TAG" &
docker push "gcr.io/$PREFIX/rockylinux8-java8" &
docker push "gcr.io/$PREFIX/rockylinux8-java8:$IMAGE_TAG" &
docker push "gcr.io/$PREFIX/rockylinux8-java11" &
docker push "gcr.io/$PREFIX/rockylinux8-java11:$IMAGE_TAG" &
docker push "gcr.io/$PREFIX/rockylinux8-java11-devtoolset10" &
docker push "gcr.io/$PREFIX/rockylinux8-java11-devtoolset10:$IMAGE_TAG" &
docker push "gcr.io/$PREFIX/rockylinux8-releaser" &
docker push "gcr.io/$PREFIX/rockylinux8-releaser:$IMAGE_TAG" &
docker push "gcr.io/$PREFIX/debian10-java11" &
docker push "gcr.io/$PREFIX/debian10-java11:$IMAGE_TAG" &
docker push "gcr.io/$PREFIX/debian12" &
docker push "gcr.io/$PREFIX/debian12:$IMAGE_TAG" &
docker push "gcr.io/$PREFIX/debian13" &
docker push "gcr.io/$PREFIX/debian13:$IMAGE_TAG" &
docker push "gcr.io/$PREFIX/ubuntu2204-java17" &
docker push "gcr.io/$PREFIX/ubuntu2204-java17:$IMAGE_TAG" &
docker push "gcr.io/$PREFIX/ubuntu2204-kythe" &
docker push "gcr.io/$PREFIX/ubuntu2204-kythe:$IMAGE_TAG" &
docker push "gcr.io/$PREFIX/ubuntu2204-bazel-java17" &
docker push "gcr.io/$PREFIX/ubuntu2204-bazel-java17:$IMAGE_TAG" &
docker push "gcr.io/$PREFIX/ubuntu2204" &
docker push "gcr.io/$PREFIX/ubuntu2204:$IMAGE_TAG" &
docker push "gcr.io/$PREFIX/ubuntu2404" &
docker push "gcr.io/$PREFIX/ubuntu2404:$IMAGE_TAG" &
docker push "gcr.io/$PREFIX/ubuntu2404-kythe" &
docker push "gcr.io/$PREFIX/ubuntu2404-kythe:$IMAGE_TAG" &
docker push "gcr.io/$PREFIX/fedora39-java17" &
docker push "gcr.io/$PREFIX/fedora39-java17:$IMAGE_TAG" &
docker push "gcr.io/$PREFIX/fedora39-bazel-java17" &
docker push "gcr.io/$PREFIX/fedora39-bazel-java17:$IMAGE_TAG" &
docker push "gcr.io/$PREFIX/fedora40-java21" &
docker push "gcr.io/$PREFIX/fedora40-java21:$IMAGE_TAG" &
docker push "gcr.io/$PREFIX/fedora40-bazel-java21" &
docker push "gcr.io/$PREFIX/fedora40-bazel-java21:$IMAGE_TAG" &
docker push "gcr.io/$PREFIX/fedora43-java25" &
docker push "gcr.io/$PREFIX/fedora43-java25:$IMAGE_TAG" &
docker push "gcr.io/$PREFIX/fedora43-bazel-java25" &
docker push "gcr.io/$PREFIX/fedora43-bazel-java25:$IMAGE_TAG" &
wait
