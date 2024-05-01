FROM fedora:40 as fedora40-bazel-java21
ARG BUILDARCH

RUN dnf update -y

### Install packages required by Bazel and its tests
RUN dnf install -y \
  bind-utils \
  dnsutils \
  dpkg-dev \
  expect \
  findutils \
  gcc \
  gcc-c++ \
  git \
  glibc-langpack-en \
  glibc-locale-source \
  iproute \
  iputils \
  lcov \
  java-21-openjdk \
  java-21-openjdk-devel \
  patch \
  perl \
  python2 \
  python3 \
  python3-devel \
  python3-pip \
  python3-requests \
  python3-setuptools \
  python3-wheel \
  python3-yaml \
  unzip \
  vim \
  wget \
  which \
  zip \
  && dnf clean all \
  && rm -rf /var/cache/yum

RUN localedef -i en_US -f ISO-8859-1 en_US.ISO-8859-1

# Allow using sudo inside the container.
RUN echo "ALL ALL=(ALL:ALL) NOPASSWD: ALL" >> /etc/sudoers

ENV JAVA_HOME /usr/lib/jvm/java-21-openjdk

FROM fedora40-bazel-java21 AS fedora40-java21

# Install Google Cloud SDK
COPY google-cloud-sdk.repo /etc/yum.repos.d/google-cloud-sdk.repo

RUN dnf install -y \
  google-cloud-sdk

# Bazelisk
RUN LATEST_BAZELISK=$(curl -sSI https://github.com/bazelbuild/bazelisk/releases/latest | grep -i '^location: ' | sed 's|.*/||' | sed $'s/\r//') && \
    curl -Lo /usr/local/bin/bazel https://github.com/bazelbuild/bazelisk/releases/download/${LATEST_BAZELISK}/bazelisk-linux-${BUILDARCH} && \
    chown root:root /usr/local/bin/bazel && \
    chmod 0755 /usr/local/bin/bazel

# Buildifier
RUN LATEST_BUILDIFIER=$(curl -sSI https://github.com/bazelbuild/buildtools/releases/latest | grep -i '^location: ' | sed 's|.*/||' | sed $'s/\r//') && \
    curl -Lo /usr/local/bin/buildifier https://github.com/bazelbuild/buildtools/releases/download/${LATEST_BUILDIFIER}/buildifier-linux-${BUILDARCH} && \
    chown root:root /usr/local/bin/buildifier && \
    chmod 0755 /usr/local/bin/buildifier
