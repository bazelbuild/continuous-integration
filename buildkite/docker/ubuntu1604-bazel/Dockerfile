FROM ubuntu:16.04 as ubuntu1604-bazel-nojava
ENV DEBIAN_FRONTEND="noninteractive"

### Install packages required by Bazel and its tests
RUN dpkg --add-architecture i386 && \
    apt-get -qqy update && \
    echo "Installing base packages" && \
    apt-get -qqy install --no-install-recommends apt-utils curl lsb-release software-properties-common && \
    echo "Installing packages required by Bazel" && \
    apt-get -qqy install --no-install-recommends build-essential coreutils clang curl ed expect file git iproute2 iputils-ping libbz2-1.0:i386 libncurses5:i386 libssl-dev libstdc++6:i386 libz1:i386 less netcat-openbsd python python-dev python-six python3 python3-dev python3-six unzip wget xvfb zip zlib1g-dev && \
    echo "Installing packages required by C++ coverage tests" && \
    apt-get -qqy install --no-install-recommends lcov llvm && \
    echo "Installing packages required by Bazel (Ubuntu 16.04 only)" && \
    apt-get -qqy install --no-install-recommends realpath && \
    apt-get -qqy purge apport && \
    rm -rf /var/lib/apt/lists/*

FROM ubuntu1604-bazel-nojava AS ubuntu1604-bazel-java8
RUN apt-get -qqy update && \
    apt-get -qqy install openjdk-8-jdk && \
    rm -rf /var/lib/apt/lists/*

### Required by rbe_autoconfig
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64/
ENV LANG "C.UTF-8"
ENV LANGUAGE "C.UTF-8"
ENV LC_ALL "C.UTF-8"
