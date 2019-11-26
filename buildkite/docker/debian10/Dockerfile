FROM debian:10 as debian10-nojava
ENV DEBIAN_FRONTEND="noninteractive"
ARG BUILDARCH
COPY --from=gcr.io/bazel-public/base:bazelisk /usr/local/bin/bazel /usr/local/bin/bazel
COPY --from=gcr.io/bazel-public/base:buildifier /usr/local/bin/buildifier /usr/local/bin/buildifier
COPY --from=gcr.io/bazel-public/base:github-release /usr/local/bin/github-release /usr/local/bin/github-release
COPY --from=gcr.io/bazel-public/base:saucelabs /usr/local/bin/sc /usr/local/bin/sc

### Install required packages.
RUN dpkg --add-architecture i386 && \
    apt-get -qqy update && \
    echo "Installing base packages" && \
    apt-get -qqy install apt-utils curl lsb-release software-properties-common && \
    echo "Installing packages required by Bazel" && \
    apt-get -qqy install bind9-host build-essential clang curl dnsutils ed git iproute2 iputils-ping netcat-openbsd python python-dev python3 python3-dev unzip wget xvfb zip zlib1g-dev && \
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
    echo "Installing packages required by rules_haskell" && \
    apt-get -qqy install libgmp-dev && \
    apt-get -qqy purge apport && \
    rm -rf /var/lib/apt/lists/*

### Install Python packages required by Tensorflow.
RUN pip install keras_applications keras_preprocessing && \
    pip3 install keras_applications keras_preprocessing

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
    curl -sSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
    add-apt-repository "deb [arch=$BUILDARCH] https://download.docker.com/linux/debian $(lsb_release -cs) stable" && \
    apt-get -qqy update && \
    apt-get -qqy install docker-ce && \
    rm -rf /var/lib/apt/lists/*

### Install Node.js and packages required by Gerrit.
### (see https://gerrit.googlesource.com/gerrit/+show/master/polygerrit-ui/README.md)
RUN curl -L https://deb.nodesource.com/setup_10.x | bash - && \
    apt-get -qqy update && \
    apt-get -qqy install nodejs && \
    npm install --unsafe-perm -g \
    eslint@"=4.19.0" \
    eslint-config-google@"=0.12.0" \
    eslint-plugin-html@"=5.0.3" \
    eslint-plugin-promise@"=4.0.1" \
    typescript \
    fried-twinkie@"^0.2.2" \
    polylint polymer-cli \
    web-component-tester@6.8.0 && \
    rm -rf /var/lib/apt/lists/*

### Install Python dependencies required by our own bazelci.py script.
RUN pip3 install requests uritemplate pyyaml github3.py

### Install Go.
ENV GO_HOME "/opt/go1.13.4.linux-amd64"
ENV PATH "${PATH}:${GO_HOME}/bin"

### Install Swift toolchain (required by rules_swift).
ENV SWIFT_HOME "/opt/swift-4.2.1-RELEASE-ubuntu18.04"
ENV PATH "${PATH}:${SWIFT_HOME}/usr/bin"

FROM debian10-nojava AS debian10-java11
RUN apt-get -qqy update && \
    apt-get -qqy install openjdk-11-jdk && \
    rm -rf /var/lib/apt/lists/*
