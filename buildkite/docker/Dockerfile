FROM ubuntu AS builder
ENV DEBIAN_FRONTEND="noninteractive"
RUN apt-get -qqy update && \
    apt-get -qqy install curl openjdk-8-jre-headless unzip && \
    rm -rf /var/lib/apt/lists/*

FROM builder AS bazelisk
RUN curl -Lo /usr/local/bin/bazel https://github.com/bazelbuild/bazelisk/releases/download/v0.0.5/bazelisk-linux-amd64 && \
    chown root:root /usr/local/bin/bazel && \
    chmod 0755 /usr/local/bin/bazel

FROM builder AS buildifier
RUN LATEST_BUILDIFIER=$(curl -sSI https://github.com/bazelbuild/buildtools/releases/latest | grep '^Location: ' | sed 's|.*/||' | sed $'s/\r//') && \
    curl -Lo /usr/local/bin/buildifier https://github.com/bazelbuild/buildtools/releases/download/${LATEST_BUILDIFIER}/buildifier && \
    chown root:root /usr/local/bin/buildifier && \
    chmod 0755 /usr/local/bin/buildifier

### Install tools required by the release process.
FROM builder AS github-release
RUN curl -L https://github.com/c4milo/github-release/releases/download/v1.1.0/github-release_v1.1.0_linux_amd64.tar.gz | \
    tar xz -C /usr/local/bin && \
    chown root:root /usr/local/bin/github-release && \
    chmod 0755 /usr/local/bin/github-release

### Install Sauce Connect (for rules_webtesting).
FROM builder AS saucelabs
RUN curl -L https://saucelabs.com/downloads/sc-4.5.3-linux.tar.gz | \
    tar xz -C /usr/local --strip=1 sc-4.5.3-linux/bin/sc && \
    chown root:root /usr/local/bin/sc && \
    chmod 0755 /usr/local/bin/sc

###############################################################################
### UBUNTU 16.04 ##############################################################
###############################################################################

FROM ubuntu:16.04 as ubuntu1604-nojava
ENV DEBIAN_FRONTEND="noninteractive"
COPY --from=bazelisk /usr/local/bin/bazel /usr/local/bin/bazel
COPY --from=buildifier /usr/local/bin/buildifier /usr/local/bin/buildifier
COPY --from=github-release /usr/local/bin/github-release /usr/local/bin/github-release
COPY --from=saucelabs /usr/local/bin/sc /usr/local/bin/sc

### Install required packages.
RUN dpkg --add-architecture i386 && \
    apt-get -qqy update && \
    echo "Installing base packages" && \
    apt-get -qqy install apt-utils curl lsb-release software-properties-common && \
    echo "Installing packages required by Bazel" && \
    apt-get -qqy install build-essential clang curl ed git iproute2 iputils-ping netcat-openbsd python python-dev python3 python3-dev unzip wget xvfb zip zlib1g-dev && \
    echo "Installing packages required by Android SDK" && \
    apt-get -qqy install expect libbz2-1.0:i386 libncurses5:i386 libstdc++6:i386 libz1:i386 && \
    echo "Installing packages required by Tensorflow" && \
    apt-get -qqy install libcurl3-dev swig python-enum34 python-mock python-numpy python-pip python-wheel python3-mock python3-numpy python3-pip python3-wheel && \
    echo "Installing packages required by Envoy" && \
    apt-get -qqy install automake autotools-dev cmake libtool m4 ninja-build && \
    echo "Installing packages required by Android emulator" && \
    apt-get -qqy install cpio cpu-checker lsof qemu-kvm qemu-system-x86 unzip xvfb && \
    echo "Installing packages required by Bazel release process" && \
    apt-get -qqy install devscripts gnupg pandoc reprepro && \
    echo "Installing packages required by C++ coverage tests" && \
    apt-get -qqy install lcov llvm && \
    echo "Installing packages required by Swift toolchain" && \
    apt-get -qqy install clang libicu-dev && \
    echo "Installing packages required by rules_webtesting" && \
    apt-get -qqy install python-urllib3 python3-urllib3 && \
    echo "Installing packages required by Kythe" && \
    apt-get -qqy install bison flex uuid-dev asciidoc graphviz source-highlight && \
    echo "Installing packages required by upb" && \
    apt-get -qqy install libreadline-dev && \
    echo "Installing packages required by Bazel (Ubuntu 14.04 and 16.04 only)" && \
    apt-get -qqy install realpath libssl-dev && \
    apt-get -qqy purge apport && \
    rm -rf /var/lib/apt/lists/*

### Install Python packages required by Tensorflow.
RUN pip install keras_applications keras_preprocessing future && \
    pip3 install keras_applications keras_preprocessing future

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

### Install Node.js and packages required by Gerrit.
### (see https://gerrit.googlesource.com/gerrit/+show/master/polygerrit-ui/README.md)
RUN curl -L https://deb.nodesource.com/setup_8.x | bash - && \
    apt-get -qqy update && \
    apt-get -qqy install nodejs && \
    npm install -g typescript fried-twinkie@0.0.15 && \
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
    pip3.6 install requests uritemplate pyyaml github3.py && \
    rm -rf "/usr/local/src/Python-${PYTHON_VERSION}"

### Install Swift toolchain (required by rules_swift).
ENV SWIFT_HOME "/opt/swift-4.2.1-RELEASE-ubuntu16.04"
ENV PATH "${PATH}:${SWIFT_HOME}/usr/bin"

### Install Go.
RUN curl -L https://dl.google.com/go/go1.12.5.linux-amd64.tar.gz | tar -C /usr/local -xz
ENV GO_HOME "/usr/local/go"
ENV PATH "${PATH}:${GO_HOME}/bin"
RUN go version

FROM ubuntu1604-nojava AS ubuntu1604-java8
RUN apt-get -qqy update && \
    apt-get -qqy install openjdk-8-jdk && \
    rm -rf /var/lib/apt/lists/*

###############################################################################
### UBUNTU 18.04 ##############################################################
###############################################################################

FROM ubuntu:18.04 as ubuntu1804-nojava
ENV DEBIAN_FRONTEND="noninteractive"
COPY --from=bazelisk /usr/local/bin/bazel /usr/local/bin/bazel
COPY --from=buildifier /usr/local/bin/buildifier /usr/local/bin/buildifier
COPY --from=github-release /usr/local/bin/github-release /usr/local/bin/github-release
COPY --from=saucelabs /usr/local/bin/sc /usr/local/bin/sc

### Install required packages.
RUN dpkg --add-architecture i386 && \
    apt-get -qqy update && \
    echo "Installing base packages" && \
    apt-get -qqy install apt-utils curl lsb-release software-properties-common && \
    echo "Installing packages required by Bazel" && \
    apt-get -qqy install build-essential clang curl ed git iproute2 iputils-ping netcat-openbsd python python-dev python3 python3-dev unzip wget xvfb zip zlib1g-dev && \
    echo "Installing packages required by Android SDK" && \
    apt-get -qqy install expect libbz2-1.0:i386 libncurses5:i386 libstdc++6:i386 libz1:i386 && \
    echo "Installing packages required by Tensorflow" && \
    apt-get -qqy install libcurl3-dev swig python-enum34 python-mock python-numpy python-pip python-wheel python3-mock python3-numpy python3-pip python3-wheel && \
    echo "Installing packages required by Envoy" && \
    apt-get -qqy install automake autotools-dev cmake libtool m4 ninja-build && \
    echo "Installing packages required by Android emulator" && \
    apt-get -qqy install cpio cpu-checker lsof qemu-kvm qemu-system-x86 unzip xvfb && \
    echo "Installing packages required by Bazel release process" && \
    apt-get -qqy install devscripts gnupg pandoc reprepro && \
    echo "Installing packages required by C++ coverage tests" && \
    apt-get -qqy install lcov llvm && \
    echo "Installing packages required by Swift toolchain" && \
    apt-get -qqy install clang libicu-dev && \
    echo "Installing packages required by rules_webtesting" && \
    apt-get -qqy install python-urllib3 python3-urllib3 && \
    echo "Installing packages required by Kythe" && \
    apt-get -qqy install bison flex uuid-dev asciidoc graphviz source-highlight && \
    echo "Installing packages required by upb" && \
    apt-get -qqy install libreadline-dev && \
    apt-get -qqy purge apport && \
    rm -rf /var/lib/apt/lists/*

### Install Python packages required by Tensorflow.
RUN pip install keras_applications keras_preprocessing future && \
    pip3 install keras_applications keras_preprocessing future

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

### Install Node.js and packages required by Gerrit.
### (see https://gerrit.googlesource.com/gerrit/+show/master/polygerrit-ui/README.md)
RUN curl -L https://deb.nodesource.com/setup_8.x | bash - && \
    apt-get -qqy install nodejs && \
    npm install -g typescript fried-twinkie@0.0.15 && \
    rm -rf /var/lib/apt/lists/*

### Install Python dependencies required by our own bazelci.py script.
RUN pip3 install requests uritemplate pyyaml github3.py

### Install Swift toolchain (required by rules_swift).
ENV SWIFT_HOME "/opt/swift-4.2.1-RELEASE-ubuntu18.04"
ENV PATH "${PATH}:${SWIFT_HOME}/usr/bin"

### Install Go.
RUN curl -L https://dl.google.com/go/go1.12.5.linux-amd64.tar.gz | tar -C /usr/local -xz
ENV GO_HOME "/usr/local/go"
ENV PATH "${PATH}:${GO_HOME}/bin"
RUN go version

FROM ubuntu1804-nojava AS ubuntu1804-java11
RUN apt-get -qqy update && \
    apt-get -qqy install openjdk-11-jdk && \
    rm -rf /var/lib/apt/lists/*
