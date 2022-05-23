# ATTENTION: use the build.sh script to build this image.
# ./build.sh <OCI_REPOSITORY> <BAZEL_VERSION>

FROM ubuntu:16.04 AS base_image

RUN --mount=source=bazel/oci/install_packages.sh,target=/mnt/install_packages.sh,type=bind \
    /mnt/install_packages.sh

FROM base_image AS downloader

ARG BAZEL_VERSION

WORKDIR /var/bazel
RUN --mount=source=bazel/oci/install_bazel.sh,target=/mnt/install_bazel.sh,type=bind \
    /mnt/install_bazel.sh

FROM base_image

RUN useradd --system --create-home --home-dir=/home/ubuntu --shell=/bin/bash --gid=root --groups=sudo --uid=1000 ubuntu
USER ubuntu
WORKDIR /home/ubuntu
COPY --from=downloader /var/bazel/bazel /usr/local/bin/bazel
ENTRYPOINT ["/usr/local/bin/bazel"]
