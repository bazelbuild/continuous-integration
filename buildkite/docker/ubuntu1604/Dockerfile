FROM ubuntu:16.04 as java8

ENV DEBIAN_FRONTEND "noninteractive"

RUN apt-get -qqy update && \
    apt-get -qqy install lsb-release curl apt-utils software-properties-common && \
    rm -rf /var/lib/apt/lists/*

### Install Google Cloud SDK.
### https://cloud.google.com/sdk/docs/quickstart-debian-ubuntu
RUN export CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)" && \
    echo "deb http://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl -L https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
    apt-get -qqy update && apt-get -qqy install google-cloud-sdk && \
    rm -rf /var/lib/apt/lists/*

### Install required packages.
RUN dpkg --add-architecture i386 && \
    apt-get -qqy update && \
    echo "Installing packages required by Bazel" && \
    apt-get -qqy install build-essential clang curl git python python-dev python3 python3-dev unzip wget xvfb zip zlib1g-dev && \
    echo "Installing packages required by Android SDK" && \
    apt-get -qqy install expect libbz2-1.0:i386 libncurses5:i386 libstdc++6:i386 libz1:i386 && \
    echo "Installing packages required by Tensorflow" && \
    apt-get -qqy install libcurl3-dev swig python-enum34 python-mock python-numpy python-pip python-wheel python3-mock python3-numpy python3-pip python3-wheel && \
    pip install keras_applications keras_preprocessing && \
    pip3 install keras_applications keras_preprocessing && \
    echo "Installing packages required by Envoy" && \
    apt-get -qqy install automake autotools-dev cmake libtool m4 && \
    echo "Installing packages required by Android emulator" && \
    apt-get -qqy install cpu-checker qemu-system-x86 unzip xvfb && \
    echo "Installing packages required by Bazel release process" && \
    apt-get -qqy install devscripts gnupg pandoc reprepro ssmtp && \
    echo "Installing packages required by C++ coverage tests" && \
    apt-get -qqy install lcov llvm && \
    echo "Installing packages required by Swift toolchain" && \
    apt-get -qqy install clang libicu-dev && \
    echo "Installing packages required by Bazel (Ubuntu 14.04 and 16.04 only)" && \
    apt-get -qqy install realpath libssl-dev && \
    apt-get -qqy purge apport && \
    rm -rf /var/lib/apt/lists/*

### Install Bazelisk (as Bazel).
RUN curl -Lo /usr/local/bin/bazel https://raw.githubusercontent.com/philwo/bazelisk/master/bazelisk.py && \
    chmod 0755 /usr/local/bin/bazel

### Install Azul Zulu.
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 0x219BD9C9 && \
    apt-add-repository 'deb http://repos.azulsystems.com/ubuntu stable main' && \
    apt-get -qqy update && \
    apt-get -qqy install zulu-8

### Install Mono.
RUN apt-get -qqy install apt-transport-https ca-certificates && \
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF && \
    add-apt-repository "deb https://download.mono-project.com/repo/ubuntu stable-$(lsb_release -cs) main" && \
    apt-get -qqy update && \
    apt-get -qqy install mono-devel mono-complete

### Install Node.js.
RUN curl -L https://deb.nodesource.com/setup_8.x | bash - && \
    apt-get -qqy install nodejs

### Required by Gerrit.
### https://gerrit.googlesource.com/gerrit/+show/master/polygerrit-ui/README.md
RUN npm install -g typescript fried-twinkie@0.0.15

### Install Python.
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

### Install Android NDK.
ENV ANDROID_NDK_HOME "/opt/android-ndk-r15c"
RUN cd /opt && \
    curl -Lo android-ndk.zip https://dl.google.com/android/repository/android-ndk-r15c-linux-x86_64.zip && \
    unzip android-ndk.zip > /dev/null && \
    rm android-ndk.zip

### Install Android SDK.
ENV ANDROID_HOME "/opt/android-sdk-linux"
RUN mkdir -p /opt/android-sdk-linux && \
    cd /opt/android-sdk-linux && \
    curl -Lo android-sdk.zip https://dl.google.com/android/repository/sdk-tools-linux-4333796.zip && \
    unzip android-sdk.zip > /dev/null && \
    rm android-sdk.zip && \
    yes | tools/bin/sdkmanager --licenses > /dev/null && \
    tools/bin/sdkmanager --update && \
    tools/bin/sdkmanager \
    "build-tools;27.0.3" \
    "build-tools;28.0.2" \
    "emulator" \
    "extras;android;m2repository" \
    "platform-tools" \
    "platforms;android-24" \
    "platforms;android-28" \
    "system-images;android-19;default;x86" \
    "system-images;android-21;default;x86" \
    "system-images;android-22;default;x86" \
    "system-images;android-23;default;x86"

### Install Swift toolchain (for rules_swift).
ENV SWIFT_HOME "/opt/swift"
ENV PATH "${PATH}:${SWIFT_HOME}/usr/bin"
RUN mkdir -p /opt/swift && \
    curl -L https://swift.org/builds/swift-4.2.1-release/ubuntu1604/swift-4.2.1-RELEASE/swift-4.2.1-RELEASE-ubuntu16.04.tar.gz | \
    tar xz -C /opt/swift --strip 1

### Install tools required by the release process.
RUN curl -L https://github.com/c4milo/github-release/releases/download/v1.1.0/github-release_v1.1.0_linux_amd64.tar.gz | \
    tar xz -C /usr/local/bin && \
    chown root:root /usr/local/bin/github-release && \
    chmod 0755 /usr/local/bin/github-release

### Install Sauce Connect (for rules_webtesting).
RUN curl -L https://saucelabs.com/downloads/sc-4.5.1-linux.tar.gz | \
    tar xz -C /opt && \
    chown -R root:root /opt/sc-4.5.1-linux && \
    ln -s /opt/sc-4.5.1-linux/bin/sc /usr/local/bin/sc
