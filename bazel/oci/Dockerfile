# ATTENTION: use the build.sh script to build this image.
# ./build.sh <OCI_REPOSITORY> <BAZEL_VERSION>

# When upgrading the base OS image, update the SHA as well to keep the image pinned.
FROM ubuntu:20.04@sha256:626ffe58f6e7566e00254b638eb7e0f3b11d4da9675088f4781a50ae288f3322 AS base_image

RUN apt-get update && \
    DEBIAN_FRONTEND="noninteractive" \
    TZ="Etc/UTC" \
    apt-get install --yes \
        build-essential \
        curl \
        git \
        openjdk-11-jdk \
        python3 \
        python3-pip \
        unzip \
        zip

FROM base_image AS downloader

ARG BAZEL_VERSION

WORKDIR /var/bazel
RUN curl \
        --fail \
        --fail-early \
        --no-progress-meter \
        --location \
        --remote-name \
        "https://github.com/bazelbuild/bazel/releases/download/${BAZEL_VERSION}/bazel-${BAZEL_VERSION}-linux-x86_64"
RUN curl \
        --fail \
        --fail-early \
        --no-progress-meter \
        --location \
        "https://github.com/bazelbuild/bazel/releases/download/${BAZEL_VERSION}/bazel-${BAZEL_VERSION}-linux-x86_64.sha256" \
    | sha256sum --check \
    && mv "bazel-${BAZEL_VERSION}-linux-x86_64" bazel \
    && chmod +x bazel

FROM base_image

COPY --from=downloader /var/bazel/bazel /usr/local/bin/bazel
ENTRYPOINT ["/usr/local/bin/bazel"]
