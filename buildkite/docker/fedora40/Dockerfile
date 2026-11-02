FROM fedora:40 AS fedora40-bazel-java21
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
  google-cloud-cli

# Bazelisk
COPY --from=tools --chmod=0755 bazelisk-linux-${BUILDARCH} /usr/local/bin/bazel

# Buildifier
COPY --from=tools --chmod=0755 buildifier-linux-${BUILDARCH} /usr/local/bin/buildifier
