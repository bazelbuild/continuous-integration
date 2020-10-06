FROM ubuntu AS builder
ENV DEBIAN_FRONTEND="noninteractive"
RUN apt-get -qqy update && \
    apt-get -qqy install curl openjdk-8-jre-headless unzip && \
    rm -rf /var/lib/apt/lists/*

FROM builder AS bazelisk
RUN curl -Lo /usr/local/bin/bazel https://github.com/bazelbuild/bazelisk/releases/download/v1.7.4/bazelisk-linux-arm64 && \
    chown root:root /usr/local/bin/bazel && \
    chmod 0755 /usr/local/bin/bazel

### Install tools required by the release process.
FROM builder AS github-release
RUN curl -L https://github.com/c4milo/github-release/releases/download/v1.1.0/github-release_v1.1.0_linux_arm64.tar.gz | \
    tar xz -C /usr/local/bin && \
    chown root:root /usr/local/bin/github-release && \
    chmod 0755 /usr/local/bin/github-release
