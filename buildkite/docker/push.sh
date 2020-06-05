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

docker push "gcr.io/$PREFIX/centos7-java8"
docker push "gcr.io/$PREFIX/centos7-releaser"
docker push "gcr.io/$PREFIX/debian10-java11"
docker push "gcr.io/$PREFIX/ubuntu1604-bazel-java8"
docker push "gcr.io/$PREFIX/ubuntu1604-java8"
docker push "gcr.io/$PREFIX/ubuntu1804-bazel-java11"
docker push "gcr.io/$PREFIX/ubuntu1804-java11"
docker push "gcr.io/$PREFIX/ubuntu1804-nojava"
docker push "gcr.io/$PREFIX/ubuntu2004-bazel-java11"
docker push "gcr.io/$PREFIX/ubuntu2004-java11"
docker push "gcr.io/$PREFIX/ubuntu2004-java11-kythe"
docker push "gcr.io/$PREFIX/ubuntu2004-nojava"
