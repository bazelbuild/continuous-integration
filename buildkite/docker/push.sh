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

# Containers used by Bazel CI
docker push "gcr.io/$PREFIX/rockylinux8" &
docker push "gcr.io/$PREFIX/rockylinux8-java8" &
docker push "gcr.io/$PREFIX/rockylinux8-java11" &
docker push "gcr.io/$PREFIX/rockylinux8-java11-devtoolset10" &
docker push "gcr.io/$PREFIX/rockylinux8-releaser" &
docker push "gcr.io/$PREFIX/debian10-java11" &
docker push "gcr.io/$PREFIX/debian11-java17" &
docker push "gcr.io/$PREFIX/ubuntu1804-bazel-java11" &
docker push "gcr.io/$PREFIX/ubuntu1804-java11" &
docker push "gcr.io/$PREFIX/ubuntu2004-bazel-java11" &
docker push "gcr.io/$PREFIX/ubuntu2004-java11" &
docker push "gcr.io/$PREFIX/ubuntu2004" &
docker push "gcr.io/$PREFIX/ubuntu2204-java17" &
docker push "gcr.io/$PREFIX/ubuntu2204-kythe" &
docker push "gcr.io/$PREFIX/ubuntu2204-bazel-java17" &
docker push "gcr.io/$PREFIX/ubuntu2204" &
docker push "gcr.io/$PREFIX/ubuntu2404" &
docker push "gcr.io/$PREFIX/ubuntu2404-kythe" &
docker push "gcr.io/$PREFIX/fedora39-java17" &
docker push "gcr.io/$PREFIX/fedora39-bazel-java17" &
docker push "gcr.io/$PREFIX/fedora40-java21" &
docker push "gcr.io/$PREFIX/fedora40-bazel-java21" &
wait
