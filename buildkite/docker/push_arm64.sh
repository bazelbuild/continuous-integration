#!/bin/bash
# TODO(fweikert): merge this file into push.sh once ARM64 support is no longer experimental

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

docker buildx builder prune -a -f
docker buildx buildx create --name cibuilder --use

# Containers used by Bazel CI
docker buildx build --push -f centos7/Dockerfile    --target centos7           --platform linux/arm64,linux/amd64 -t "gcr.io/$PREFIX/centos7" centos7 &
docker buildx build --push -f debian10/Dockerfile   --target debian10-java11   --platform linux/arm64,linux/amd64 -t "gcr.io/$PREFIX/debian10-java11" debian10 &
docker buildx build --push -f debian11/Dockerfile   --target debian11-java17   --platform linux/arm64,linux/amd64 -t "gcr.io/$PREFIX/debian11-java17" debian11 &
docker buildx build --push -f ubuntu1604/Dockerfile --target ubuntu1604-java8  --platform linux/arm64,linux/amd64 -t "gcr.io/$PREFIX/ubuntu1604-java8" ubuntu1604 &
docker buildx build --push -f ubuntu1804/Dockerfile --target ubuntu1804-java11 --platform linux/arm64,linux/amd64 -t "gcr.io/$PREFIX/ubuntu1804-java11" ubuntu1804 &
docker buildx build --push -f ubuntu2004/Dockerfile --target ubuntu2004-java11 --platform linux/arm64,linux/amd64 -t "gcr.io/$PREFIX/ubuntu2004-java11" ubuntu2004 &
docker buildx build --push -f ubuntu2204/Dockerfile --target ubuntu2204-java17 --platform linux/arm64,linux/amd64 -t "gcr.io/$PREFIX/ubuntu2204-java17" ubuntu2204 &
wait

docker buildx build --push -f centos7/Dockerfile    --target centos7-java8               --platform linux/arm64,linux/amd64 -t "gcr.io/$PREFIX/centos7-java8" centos7
docker buildx build --push -f centos7/Dockerfile    --target centos7-java11              --platform linux/arm64,linux/amd64 -t "gcr.io/$PREFIX/centos7-java11" centos7
docker buildx build --push -f centos7/Dockerfile    --target centos7-java11-devtoolset10 --platform linux/arm64,linux/amd64 -t "gcr.io/$PREFIX/centos7-java11-devtoolset10" centos7
docker buildx build --push -f centos7/Dockerfile    --target centos7-releaser            --platform linux/arm64,linux/amd64 -t "gcr.io/$PREFIX/centos7-releaser" centos7
docker buildx build --push -f ubuntu1604/Dockerfile --target ubuntu1604-bazel-java8      --platform linux/arm64,linux/amd64 -t "gcr.io/$PREFIX/ubuntu1604-bazel-java8" ubuntu1604
docker buildx build --push -f ubuntu1804/Dockerfile --target ubuntu1804-bazel-java11     --platform linux/arm64,linux/amd64 -t "gcr.io/$PREFIX/ubuntu1804-bazel-java11" ubuntu1804
docker buildx build --push -f ubuntu2004/Dockerfile --target ubuntu2004-bazel-java11     --platform linux/arm64,linux/amd64 -t "gcr.io/$PREFIX/ubuntu2004-bazel-java11" ubuntu2004
docker buildx build --push -f ubuntu2004/Dockerfile --target ubuntu2004-java11-kythe     --platform linux/arm64,linux/amd64 -t "gcr.io/$PREFIX/ubuntu2004-java11-kythe" ubuntu2004
docker buildx build --push -f ubuntu2204/Dockerfile --target ubuntu2204-bazel-java17     --platform linux/arm64,linux/amd64 -t "gcr.io/$PREFIX/ubuntu2204-bazel-java17" ubuntu2204
