FROM ubuntu AS builder
ENV DEBIAN_FRONTEND="noninteractive"
RUN apt-get -qqy update && \
    apt-get -qqy install curl openjdk-8-jre-headless unzip && \
    rm -rf /var/lib/apt/lists/*

FROM builder AS bazelisk
RUN curl -Lo /usr/local/bin/bazel https://github.com/bazelbuild/bazelisk/releases/download/v0.0.8/bazelisk-linux-amd64 && \
    chown root:root /usr/local/bin/bazel && \
    chmod 0755 /usr/local/bin/bazel

FROM builder AS buildifier
RUN LATEST_BUILDIFIER=$(curl -sSI https://github.com/bazelbuild/buildtools/releases/latest | grep '^Location: ' | sed 's|.*/||' | sed $'s/\r//') && \
    curl -Lo /usr/local/bin/buildifier https://github.com/bazelbuild/buildtools/releases/download/${LATEST_BUILDIFIER}/buildifier && \
    chown root:root /usr/local/bin/buildifier && \
    chmod 0755 /usr/local/bin/buildifier

### Install tools required by the release process.
FROM builder AS github-release
RUN curl -L https://github.com/c4milo/github-release/releases/download/v1.1.0/github-release_v1.1.0_linux_amd64.tar.gz | \
    tar xz -C /usr/local/bin && \
    chown root:root /usr/local/bin/github-release && \
    chmod 0755 /usr/local/bin/github-release

### Install Sauce Connect (for rules_webtesting).
FROM builder AS saucelabs
RUN curl -L https://saucelabs.com/downloads/sc-4.5.3-linux.tar.gz | \
    tar xz -C /usr/local --strip=1 sc-4.5.3-linux/bin/sc && \
    chown root:root /usr/local/bin/sc && \
    chmod 0755 /usr/local/bin/sc

### Install Go.
# FROM builder AS go
# RUN curl -L https://dl.google.com/go/go1.12.5.linux-amd64.tar.gz | \
#     tar xz -C /usr/local
