FROM ubuntu:26.04 AS ubuntu2604-bazel-nojdk
ARG TARGETARCH

ENV DEBIAN_FRONTEND="noninteractive"
ENV LANG "C.UTF-8"
ENV LANGUAGE "C.UTF-8"
ENV LC_ALL "C.UTF-8"

### Install packages required by Bazel and its tests
RUN apt-get -y update && \
    apt-get -y install --no-install-recommends \
    apt-utils \
    bind9-host \
    build-essential \
    clang \
    clang-tools \
    coreutils \
    curl \
    dnsutils \
    ed \
    expect \
    file \
    git \
    gnupg2 \
    golang \
    iproute2 \
    iputils-ping \
    lcov \
    less \
    libclang-rt-dev \
    libc++-dev \
    libssl-dev \
    llvm \
    llvm-dev \
    lsb-release \
    locales \
    netcat-openbsd \
    openssh-client \
    python-is-python3 \
    python3 \
    python3-dev \
    python3-pip \
    python3-requests \
    python3-setuptools \
    python3-six \
    python3-wheel \
    python3-yaml \
    software-properties-common \
    sudo \
    unzip \
    vim \
    wget \
    zip \
    zlib1g-dev \
    && \
    apt-get -y purge apport && \
    rm -rf /var/lib/apt/lists/*

# Allow using sudo inside the container.
RUN echo "ALL ALL=(ALL:ALL) NOPASSWD: ALL" >> /etc/sudoers

# Ensure that Bazel can use its beloved ISO-8859-1 locale.
RUN localedef -i en_US -f ISO-8859-1 en_US.ISO-8859-1

FROM ubuntu2604-bazel-nojdk AS ubuntu2604-nojdk

### Install Google Cloud CLI.
### https://cloud.google.com/sdk/docs/quickstart-debian-ubuntu
### apt-key was removed in Ubuntu 26.04 (APT 3.2); use gpg --dearmor (gpg is already installed).
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
    apt-get update -y && apt-get install google-cloud-cli -y && \
    rm -rf /var/lib/apt/lists/*

# Bazelisk
COPY --from=tools --chmod=0755 bazelisk-linux-${TARGETARCH} /usr/local/bin/bazel

# Buildifier
COPY --from=tools --chmod=0755 buildifier-linux-${TARGETARCH} /usr/local/bin/buildifier

FROM ubuntu2604-nojdk AS ubuntu2604

RUN apt-get -y update && \
    apt-get -y install openjdk-25-jdk-headless && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME /usr/lib/jvm/java-25-openjdk-${TARGETARCH}
# Authoritative target container image used by rules/rbe_config.bzl to automatically activate
# --exec_mode=host and prevent toolchain/ABI discrepancies in CI.
ENV RBE_CONFIG_CONTAINER="gcr.io/bazel-public/ubuntu2604:latest"

FROM ubuntu2604 AS ubuntu2604-kythe

RUN LATEST_KYTHE=v0.0.75 && \
    mkdir /usr/local/kythe && \
    curl -fsSL "https://github.com/kythe/kythe/releases/download/${LATEST_KYTHE}/kythe-${LATEST_KYTHE}.tar.gz" | \
    tar xvz --no-same-owner --strip-components 1 --directory /usr/local/kythe && \
    chmod -R a+rw /usr/local/kythe && \
    test -f /usr/local/kythe/WORKSPACE
