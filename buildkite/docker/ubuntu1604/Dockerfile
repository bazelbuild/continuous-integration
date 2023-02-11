FROM ubuntu:16.04 as ubuntu1604-bazel-java8
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
    openjdk-8-jdk-headless \
    python \
    python-dev \
    python-six \
    python3 \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-six \
    python3-wheel \
    realpath \
    software-properties-common \
    sudo \
    unzip \
    wget \
    zip \
    zlib1g-dev \
    && \
    apt-get -y purge apport && \
    rm -rf /var/lib/apt/lists/*

# Allow using sudo inside the container.
RUN echo "ALL ALL=(ALL:ALL) NOPASSWD: ALL" >> /etc/sudoers

ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-${BUILDARCH}

FROM ubuntu1604-bazel-java8 AS ubuntu1604-java8

RUN mkdir -p /usr/local/src
COPY requirements.txt /usr/local/src/requirements.txt

### Install Python (required by our own bazelci.py script).
RUN export PYTHON_VERSION="3.6.14" && \
    cd /usr/local/src && \
    curl -LO "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz" && \
    tar xfJ "Python-${PYTHON_VERSION}.tar.xz" && \
    rm "Python-${PYTHON_VERSION}.tar.xz" && \
    cd "Python-${PYTHON_VERSION}" && \
    echo "_ssl _ssl.c -DUSE_SSL -I/usr/include -I/usr/include/openssl -L/usr/lib -lssl -lcrypto" >> Modules/Setup.dist && \
    echo "Compiling Python ${PYTHON_VERSION} ..." && \
    ./configure --quiet --enable-ipv6 && \
    make -s -j all && \
    echo "Installing Python ${PYTHON_VERSION} ..." && \
    make -s altinstall && \
    pip3.6 install --require-hashes -r requirements.txt requests==2.22.0 pyyaml==3.13 && \
    rm -rf "/usr/local/src/Python-${PYTHON_VERSION}"

### Install Google Cloud SDK.
### https://cloud.google.com/sdk/docs/quickstart-debian-ubuntu
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get update -y && apt-get install google-cloud-sdk -y && \
    rm -rf /var/lib/apt/lists/*

### Docker (for legacy rbe_autoconfig)
RUN apt-get -y update && \
    apt-get -y install apt-transport-https ca-certificates && \
    curl -sSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - && \
    add-apt-repository "deb [arch=$BUILDARCH] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" && \
    apt-get -y update && \
    apt-get -y install docker-ce && \
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
