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

# Enable use of buildkit for all builds. No extra support in the Dockerfile is required.
# See https://docs.docker.com/develop/develop-images/build_enhancements/ for details.
export DOCKER_BUILDKIT=1

# Containers used by Bazel CI
docker build -f centos7/Dockerfile    --target centos7           -t "gcr.io/$PREFIX/centos7" centos7 &
docker build -f debian10/Dockerfile   --target debian10-java11   -t "gcr.io/$PREFIX/debian10-java11" debian10 &
docker build -f debian11/Dockerfile   --target debian11-java17   -t "gcr.io/$PREFIX/debian11-java17" debian11 &
docker build -f ubuntu1604/Dockerfile --target ubuntu1604-java8  -t "gcr.io/$PREFIX/ubuntu1604-java8" ubuntu1604 &
docker build -f ubuntu1804/Dockerfile --target ubuntu1804-java11 -t "gcr.io/$PREFIX/ubuntu1804-java11" ubuntu1804 &
docker build -f ubuntu2004/Dockerfile --target ubuntu2004-java11 -t "gcr.io/$PREFIX/ubuntu2004-java11" ubuntu2004 &
docker build -f ubuntu2204/Dockerfile --target ubuntu2204-java17 -t "gcr.io/$PREFIX/ubuntu2204-java17" ubuntu2204 &
wait

docker build -f centos7/Dockerfile    --target centos7-java8               -t "gcr.io/$PREFIX/centos7-java8" centos7
docker build -f centos7/Dockerfile    --target centos7-java11              -t "gcr.io/$PREFIX/centos7-java11" centos7
docker build -f centos7/Dockerfile    --target centos7-java11-devtoolset10 -t "gcr.io/$PREFIX/centos7-java11-devtoolset10" centos7
docker build -f centos7/Dockerfile    --target centos7-releaser            -t "gcr.io/$PREFIX/centos7-releaser" centos7
docker build -f ubuntu1604/Dockerfile --target ubuntu1604-bazel-java8      -t "gcr.io/$PREFIX/ubuntu1604-bazel-java8" ubuntu1604
docker build -f ubuntu1804/Dockerfile --target ubuntu1804-bazel-java11     -t "gcr.io/$PREFIX/ubuntu1804-bazel-java11" ubuntu1804
docker build -f ubuntu2004/Dockerfile --target ubuntu2004-bazel-java11     -t "gcr.io/$PREFIX/ubuntu2004-bazel-java11" ubuntu2004
docker build -f ubuntu2004/Dockerfile --target ubuntu2004-java11-kythe     -t "gcr.io/$PREFIX/ubuntu2004-java11-kythe" ubuntu2004
docker build -f ubuntu2204/Dockerfile --target ubuntu2204-bazel-java17     -t "gcr.io/$PREFIX/ubuntu2204-bazel-java17" ubuntu2204
