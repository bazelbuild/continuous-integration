#!/bin/bash

set -o errexit -o nounset -o pipefail

curl \
    --fail \
    --location \
    --remote-name \
    "https://github.com/bazelbuild/bazel/releases/download/${BAZEL_VERSION}/bazel-${BAZEL_VERSION}-linux-${TARGETARCH}"

curl \
    --fail \
    --location \
    "https://github.com/bazelbuild/bazel/releases/download/${BAZEL_VERSION}/bazel-${BAZEL_VERSION}-linux-${TARGETARCH}.sha256" \
    | sha256sum --check

mv "bazel-${BAZEL_VERSION}-linux-${TARGETARCH}" bazel
chmod +x bazel
