FROM ubuntu:18.04 as ubuntu1804-bazel-java11
ARG BUILDARCH

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
    coreutils \
    curl \
    dnsutils \
    ed \
    expect \
    file \
    git \
    gnupg2 \
    iproute2 \
    iputils-ping \
    lcov \
    less \
    libc++-dev \
    libssl-dev \
    llvm \
    llvm-dev \
    lsb-release \
    netcat-openbsd \
    openjdk-11-jdk-headless \
    python \
    python-dev \
    python-six \
    python3 \
    python3-dev \
    python3-pip \
    python3-requests \
    python3-setuptools \
    python3-six \
    python3-wheel \
    python3-yaml \
    software-properties-common \
    unzip \
    wget \
    zip \
    zlib1g-dev \
    && \
    apt-get -y purge apport && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-${BUILDARCH}

FROM ubuntu1804-bazel-java11 AS ubuntu1804-java11

### Install required packages.
RUN apt-get -y update && \
    echo "Installing packages required by Bazel release process" && \
    apt-get -y install devscripts pandoc reprepro && \
    echo "Installing packages required by Swift toolchain" && \
    apt-get -y install libicu-dev && \
    echo "Installing packages required by Kythe" && \
    apt-get -y install bison flex uuid-dev asciidoc graphviz source-highlight && \
    echo "Installing packages required by upb" && \
    apt-get -y install libreadline-dev && \
    echo "Installing packages required by rules_haskell" && \
    apt-get -y install libgmp-dev && \
    echo "Installing packages required by Gerrit" && \
    apt-get -y install openssh-client && \
    rm -rf /var/lib/apt/lists/*

### Install Google Cloud SDK.
### https://cloud.google.com/sdk/docs/quickstart-debian-ubuntu
RUN export CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)" && \
    echo "deb http://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl -L https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
    apt-get -y update && \
    apt-get -y install google-cloud-sdk && \
    rm -rf /var/lib/apt/lists/*

### Docker (for legacy rbe_autoconfig)
RUN apt-get -y update && \
    apt-get -y install apt-transport-https ca-certificates && \
    curl -sSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - && \
    add-apt-repository "deb [arch=$BUILDARCH] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" && \
    apt-get -y update && \
    apt-get -y install docker-ce && \
    rm -rf /var/lib/apt/lists/*

### Node.js (for Gerrit)
RUN curl -fsSL https://deb.nodesource.com/setup_14.x | bash - && \
    apt-get -y install nodejs && \
    npm install -g npm@latest && \
    rm -rf /var/lib/apt/lists/*

### Install and clang-10 (for Envoy).
RUN wget https://apt.llvm.org/llvm.sh && \
    bash llvm.sh 10 && \
    rm -f llvm.sh && \
    rm -rf /var/lib/apt/lists/*

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

# github-release
RUN LATEST_GITHUB_RELEASE=$(curl -sSI https://github.com/c4milo/github-release/releases/latest | grep -i '^location: ' | sed 's|.*/||' | sed $'s/\r//') && \
    curl -L https://github.com/c4milo/github-release/releases/download/${LATEST_GITHUB_RELEASE}/github-release_${LATEST_GITHUB_RELEASE}_linux_${BUILDARCH}.tar.gz | \
    tar xz -C /usr/local/bin && \
    chown root:root /usr/local/bin/github-release && \
    chmod 0755 /usr/local/bin/github-release

# Sauce Labs Proxy
RUN curl -L https://saucelabs.com/downloads/sc-4.6.5-linux.tar.gz | \
    tar xz -C /usr/local --strip=1 sc-4.6.5-linux/bin/sc && \
    chown root:root /usr/local/bin/sc && \
    chmod 0755 /usr/local/bin/sc
