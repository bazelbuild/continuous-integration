# ATTENTION: use the build.sh script to build this image.
# ./build.sh <OCI_REPOSITORY> <BAZEL_VERSION>

FROM ubuntu:16.04@sha256:0f71fa8d4d2d4292c3c617fda2b36f6dabe5c8b6e34c3dc5b0d17d4e704bd39c AS base_image

RUN --mount=source=bazel/oci/install_packages.sh,target=/mnt/install_packages.sh,type=bind \
    /mnt/install_packages.sh

FROM base_image AS downloader

ARG BAZEL_VERSION

WORKDIR /var/bazel
RUN --mount=source=bazel/oci/install_bazel.sh,target=/mnt/install_bazel.sh,type=bind \
    /mnt/install_bazel.sh

FROM base_image

COPY --from=downloader /var/bazel/bazel /usr/local/bin/bazel
ENTRYPOINT ["/usr/local/bin/bazel"]
