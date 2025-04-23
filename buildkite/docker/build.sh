#!/bin/bash

set -euxo pipefail

case $(git symbolic-ref --short HEAD) in
    master)
        PREFIX="bazel-public"
        ;;
    testing)
        PREFIX="bazel-public/testing"
        ;;
    *)
        echo "You must build Docker images either from the master or the testing branch!"
        exit 1
esac

# TODO docker builder prune -a -f

# Enable use of buildkit for all builds. No extra support in the Dockerfile is required.
# See https://docs.docker.com/develop/develop-images/build_enhancements/ for details.
export DOCKER_BUILDKIT=1

if [[ -z "$(docker buildx ls | grep mp-builder)" ]]; then
    docker buildx create --driver=docker-container --use --name mp-builder
fi


# Containers used by Bazel CI
docker build -f rockylinux8/Dockerfile  --builder mp-builder --platform=linux/amd64,linux/arm64 --target rockylinux8           -t "gcr.io/$PREFIX/rockylinux8"  rockylinux8 &
# docker build -f debian10/Dockerfile   --builder mp-builder --platform=linux/amd64,linux/arm64 --target debian10-java11   -t "gcr.io/$PREFIX/debian10-java11" debian10 &
# docker build -f debian11/Dockerfile   --builder mp-builder --platform=linux/amd64,linux/arm64 --target debian11-java17   -t "gcr.io/$PREFIX/debian11-java17" debian11 &
# docker build -f ubuntu1804/Dockerfile --builder mp-builder --platform=linux/amd64,linux/arm64 --target ubuntu1804-java11 -t "gcr.io/$PREFIX/ubuntu1804-java11" ubuntu1804 &
# docker build -f ubuntu2004/Dockerfile --builder mp-builder --platform=linux/amd64,linux/arm64 --target ubuntu2004-java11 -t "gcr.io/$PREFIX/ubuntu2004-java11" ubuntu2004 &
# docker build -f ubuntu2004/Dockerfile --builder mp-builder --platform=linux/amd64,linux/arm64 --target ubuntu2004        -t "gcr.io/$PREFIX/ubuntu2004" ubuntu2004 &
# docker build -f ubuntu2204/Dockerfile --builder mp-builder --platform=linux/amd64,linux/arm64 --target ubuntu2204-java17 -t "gcr.io/$PREFIX/ubuntu2204-java17" ubuntu2204 &
# docker build -f ubuntu2204/Dockerfile --builder mp-builder --platform=linux/amd64,linux/arm64 --target ubuntu2204        -t "gcr.io/$PREFIX/ubuntu2204" ubuntu2204 &
# docker build -f ubuntu2404/Dockerfile --builder mp-builder --platform=linux/amd64,linux/arm64 --target ubuntu2404        -t "gcr.io/$PREFIX/ubuntu2404" ubuntu2404 &
# docker build -f fedora39/Dockerfile   --builder mp-builder --platform=linux/amd64,linux/arm64 --target fedora39-java17   -t "gcr.io/$PREFIX/fedora39-java17" fedora39 &
# docker build -f fedora40/Dockerfile   --builder mp-builder --platform=linux/amd64,linux/arm64 --target fedora40-java21   -t "gcr.io/$PREFIX/fedora40-java21" fedora40 &
wait

docker build -f rockylinux8/Dockerfile  --builder mp-builder --platform=linux/amd64,linux/arm64 --target rockylinux8-java11              -t "gcr.io/$PREFIX/rockylinux8-java11"                rockylinux8
docker build -f rockylinux8/Dockerfile  --builder mp-builder --platform=linux/amd64,linux/arm64 --target rockylinux8-java11-devtoolset10 -t "gcr.io/$PREFIX/rockylinux8-java11-devtoolset10"   rockylinux8
docker build -f rockylinux8/Dockerfile  --builder mp-builder --platform=linux/amd64,linux/arm64 --target rockylinux8-releaser            -t "gcr.io/$PREFIX/rockylinux8-releaser"              rockylinux8
# docker build -f ubuntu1804/Dockerfile --builder mp-builder --platform=linux/amd64,linux/arm64 --target ubuntu1804-bazel-java11     -t "gcr.io/$PREFIX/ubuntu1804-bazel-java11" ubuntu1804
# docker build -f ubuntu2004/Dockerfile --builder mp-builder --platform=linux/amd64,linux/arm64 --target ubuntu2004-bazel-java11     -t "gcr.io/$PREFIX/ubuntu2004-bazel-java11" ubuntu2004
# docker build -f ubuntu2204/Dockerfile --builder mp-builder --platform=linux/amd64,linux/arm64 --target ubuntu2204-kythe            -t "gcr.io/$PREFIX/ubuntu2204-kythe" ubuntu2204
# docker build -f ubuntu2204/Dockerfile --builder mp-builder --platform=linux/amd64,linux/arm64 --target ubuntu2204-bazel-java17     -t "gcr.io/$PREFIX/ubuntu2204-bazel-java17" ubuntu2204
# docker build -f ubuntu2404/Dockerfile --builder mp-builder --platform=linux/amd64,linux/arm64 --target ubuntu2404-kythe            -t "gcr.io/$PREFIX/ubuntu2404-kythe" ubuntu2404
# docker build -f fedora39/Dockerfile   --builder mp-builder --platform=linux/amd64,linux/arm64 --target fedora39-bazel-java17       -t "gcr.io/$PREFIX/fedora39-bazel-java17" fedora39
# docker build -f fedora40/Dockerfile   --builder mp-builder --platform=linux/amd64,linux/arm64 --target fedora40-bazel-java21       -t "gcr.io/$PREFIX/fedora40-bazel-java21" fedora40
