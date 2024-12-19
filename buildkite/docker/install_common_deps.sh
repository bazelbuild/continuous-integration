#!/bin/bash

set -euxo pipefail

# Bazelisk
LATEST_BAZELISK=$(curl -sSI https://github.com/bazelbuild/bazelisk/releases/latest | grep -i '^location: ' | sed 's|.*/||' | sed $'s/\r//') && \
curl -Lo /usr/local/bin/bazel https://github.com/bazelbuild/bazelisk/releases/download/${LATEST_BAZELISK}/bazelisk-linux-${BUILDARCH} && \
chown root:root /usr/local/bin/bazel && \
chmod 0755 /usr/local/bin/bazel

# Run Bazelisk to download the latest Bazel versions.
bazelisk_latest_versions=10 && \
for i in $(seq 0 $((bazelisk_latest_versions - 1))); do \
    USE_BAZEL_VERSION="latest-$i" bazel --version; \
done

# Buildifier
LATEST_BUILDIFIER=$(curl -sSI https://github.com/bazelbuild/buildtools/releases/latest | grep -i '^location: ' | sed 's|.*/||' | sed $'s/\r//') && \
curl -Lo /usr/local/bin/buildifier https://github.com/bazelbuild/buildtools/releases/download/${LATEST_BUILDIFIER}/buildifier-linux-${BUILDARCH} && \
chown root:root /usr/local/bin/buildifier && \
chmod 0755 /usr/local/bin/buildifier
