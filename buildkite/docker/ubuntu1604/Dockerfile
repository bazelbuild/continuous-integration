FROM ubuntu:16.04 as ubuntu1604-bazel-java8
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
    openjdk-8-jdk \
    python \
    python-dev \
    python-six \
    python3 \
    python3-dev \
    python3-six \
    realpath \
    software-properties-common \
    unzip \
    wget \
    xvfb \
    zip \
    zlib1g-dev \
    && \
    apt-get -qqy purge apport && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64

FROM ubuntu1604-bazel-java8 AS ubuntu1604-java8
COPY --from=gcr.io/bazel-public/base:bazelisk /usr/local/bin/bazel /usr/local/bin/bazel
COPY --from=gcr.io/bazel-public/base:buildifier /usr/local/bin/buildifier /usr/local/bin/buildifier
COPY --from=gcr.io/bazel-public/base:saucelabs /usr/local/bin/sc /usr/local/bin/sc

### Install required packages.
RUN apt-get -qqy update && \
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

### Install Python (required by our own bazelci.py script).
RUN export PYTHON_VERSION="3.6.8" && \
    mkdir -p /usr/local/src && \
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
    pip3.6 install requests==2.22.0 pyyaml==3.13 && \
    rm -rf "/usr/local/src/Python-${PYTHON_VERSION}"

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
ENV SWIFT_HOME "/opt/swift-4.2.1-RELEASE-ubuntu16.04"
ENV PATH "${PATH}:${SWIFT_HOME}/usr/bin"
