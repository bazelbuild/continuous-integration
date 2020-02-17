FROM ubuntu:18.04 as ubuntu1804-bazel-nojava
ENV DEBIAN_FRONTEND="noninteractive"
ARG BUILDARCH

ENV LANG "C.UTF-8"
ENV LANGUAGE "C.UTF-8"
ENV LC_ALL "C.UTF-8"

### Install packages required by Bazel and its tests
RUN dpkg --add-architecture i386 && \
    apt-get -qqy update && \
    apt-get -qqy install --no-install-recommends \
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
    libbz2-1.0:i386 \
    libncurses5:i386 \
    libssl-dev \
    libstdc++6:i386 \
    libz1:i386 \
    llvm \
    llvm-dev \
    lsb-release \
    netcat-openbsd \
    python \
    python-dev \
    python-six \
    python3 \
    python3-dev \
    python3-requests \
    python3-six \
    python3-yaml \
    software-properties-common \
    unzip \
    wget \
    xvfb \
    zip \
    zlib1g-dev \
    && \
    apt-get -qqy purge apport && \
    rm -rf /var/lib/apt/lists/*

FROM ubuntu1804-bazel-nojava AS ubuntu1804-bazel-java11
RUN apt-get -qqy update && \
    apt-get -qqy install --no-install-recommends openjdk-11-jdk && \
    rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64

FROM ubuntu1804-bazel-nojava AS ubuntu1804-nojava
COPY --from=gcr.io/bazel-public/base:bazelisk /usr/local/bin/bazel /usr/local/bin/bazel
COPY --from=gcr.io/bazel-public/base:buildifier /usr/local/bin/buildifier /usr/local/bin/buildifier
COPY --from=gcr.io/bazel-public/base:saucelabs /usr/local/bin/sc /usr/local/bin/sc

### Install required packages.
RUN apt-get -qqy update && \
    echo "Installing packages required by Tensorflow" && \
    apt-get -qqy install libcurl3-dev swig python3-mock python3-numpy python3-pip python3-wheel && \
    echo "Installing packages required by Envoy" && \
    apt-get -qqy install automake autotools-dev cmake libtool m4 ninja-build && \
    echo "Installing packages required by Android emulator" && \
    apt-get -qqy install cpio cpu-checker lsof qemu-kvm qemu-system-x86 && \
    echo "Installing packages required by Bazel release process" && \
    apt-get -qqy install devscripts pandoc reprepro && \
    echo "Installing packages required by Swift toolchain" && \
    apt-get -qqy install libicu-dev && \
    echo "Installing packages required by rules_webtesting" && \
    apt-get -qqy install python-urllib3 python3-urllib3 && \
    echo "Installing packages required by Kythe" && \
    apt-get -qqy install bison flex uuid-dev asciidoc graphviz source-highlight && \
    echo "Installing packages required by upb" && \
    apt-get -qqy install libreadline-dev && \
    echo "Installing packages required by rules_haskell" && \
    apt-get -qqy install libgmp-dev && \
    echo "Installing packages required by Gerrit" && \
    apt-get -qqy install openssh-client \
    rm -rf /var/lib/apt/lists/*

### Install Python packages required by Tensorflow.
RUN pip3 install keras_applications keras_preprocessing future

### Install Google Cloud SDK.
### https://cloud.google.com/sdk/docs/quickstart-debian-ubuntu
RUN export CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)" && \
    echo "deb http://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl -L https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
    apt-get -qqy update && \
    apt-get -qqy install google-cloud-sdk && \
    rm -rf /var/lib/apt/lists/*

### Install Docker.
RUN apt-get -qqy update && \
    apt-get -qqy install apt-transport-https ca-certificates && \
    curl -sSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" && \
    apt-get -qqy update && \
    apt-get -qqy install docker-ce && \
    rm -rf /var/lib/apt/lists/*

### Install node.js (for Gerrit)
RUN curl -sL https://deb.nodesource.com/setup_12.x | bash - && \
    apt-get -qqy install nodejs && \
    rm -rf /var/lib/apt/lists/*

### Install Go.
ENV GO_HOME "/opt/go1.13.8.linux-amd64"
ENV PATH "${PATH}:${GO_HOME}/bin"

### Install Swift toolchain (required by rules_swift).
ENV SWIFT_HOME "/opt/swift-4.2.1-RELEASE-ubuntu18.04"
ENV PATH "${PATH}:${SWIFT_HOME}/usr/bin"

FROM ubuntu1804-nojava AS ubuntu1804-java11
RUN apt-get -qqy update && \
    apt-get -qqy install --no-install-recommends openjdk-11-jdk && \
    rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64
