FROM fedora:43 AS fedora43-bazel-java25
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
  jq \
  lcov \
  java-25-openjdk \
  java-25-openjdk-devel \
  patch \
  perl \
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

ENV JAVA_HOME=/usr/lib/jvm/java-25-openjdk

FROM fedora43-bazel-java25 AS fedora43-java25

# Install Google Cloud SDK
COPY google-cloud-sdk.repo /etc/yum.repos.d/google-cloud-sdk.repo

RUN dnf install -y \
  google-cloud-cli \
  && dnf clean all \
  && rm -rf /var/cache/yum

# Bazelisk
COPY --from=tools --chmod=0755 bazelisk-linux-${BUILDARCH} /usr/local/bin/bazel

# Buildifier
COPY --from=tools --chmod=0755 buildifier-linux-${BUILDARCH} /usr/local/bin/buildifier
