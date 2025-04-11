FROM rockylinux:8 AS rockylinux8-nojdk
ARG TARGETARCH

# Install required packages.
COPY google-cloud-sdk.repo /etc/yum.repos.d/google-cloud-sdk.repo

RUN dnf -y install 'dnf-command(config-manager)' && \
    dnf config-manager --set-enabled powertools && \
    dnf -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm && \
    dnf -y install \
    bind-utils \
    dpkg-dev \
    ed \
    file \
    gcc \
    gcc-c++ \
    git \
    glibc-langpack-en \
    glibc-locale-source \
    gnupg2 \
    google-cloud-sdk \
    iproute \
    lcov \
    openssl-perl \
    patch \
    python38 \
    python38-PyYAML \
    python38-requests \
    python38-six \
    rpm-build \
    sudo \
    unzip \
    which \
    zip \
    && \
    dnf clean all

# Allow using sudo inside the container.
RUN echo "ALL ALL=(ALL:ALL) NOPASSWD: ALL" >> /etc/sudoers

RUN dnf -y install dnf-utils && \
    dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo && \
    dnf -y install docker-ce docker-ce-cli containerd.io && \
    dnf clean all

# Ensure that Bazel can use its beloved ISO-8859-1 locale.
RUN localedef -i en_US -f ISO-8859-1 en_US.ISO-8859-1

# Bazelisk
RUN LATEST_BAZELISK=$(curl -sSI https://github.com/bazelbuild/bazelisk/releases/latest | grep -i '^location: ' | sed 's|.*/||' | sed $'s/\r//') && \
    curl -Lo /usr/local/bin/bazel https://github.com/bazelbuild/bazelisk/releases/download/${LATEST_BAZELISK}/bazelisk-linux-${TARGETARCH} && \
    chown root:root /usr/local/bin/bazel && \
    chmod 0755 /usr/local/bin/bazel

# Buildifier
RUN LATEST_BUILDIFIER=$(curl -sSI https://github.com/bazelbuild/buildtools/releases/latest | grep -i '^location: ' | sed 's|.*/||' | sed $'s/\r//') && \
    curl -Lo /usr/local/bin/buildifier https://github.com/bazelbuild/buildtools/releases/download/${LATEST_BUILDIFIER}/buildifier-linux-${TARGETARCH} && \
    chown root:root /usr/local/bin/buildifier && \
    chmod 0755 /usr/local/bin/buildifier

FROM rockylinux8-nojdk AS rockylinux8-nojdk-devtoolset10

RUN dnf -y install gcc-toolset-10 scl-utils && dnf clean all

FROM rockylinux8-nojdk AS rockylinux8-java8

RUN dnf -y install java-1.8.0-openjdk-devel && dnf clean all

FROM rockylinux8-nojdk AS rockylinux8-java11

RUN dnf -y install https://cdn.azul.com/zulu/bin/zulu-repo-1.0.0-1.noarch.rpm && \
    dnf -y install zulu11-jdk && \
    dnf clean all

#RUN yum install -y https://cdn.azul.com/zulu/bin/zulu-repo-1.0.0-1.noarch.rpm && \
#    yum install -y zulu11-jdk && yum clean all

FROM rockylinux8-nojdk-devtoolset10 AS rockylinux8-java11-devtoolset10

RUN dnf -y install https://cdn.azul.com/zulu/bin/zulu-repo-1.0.0-1.noarch.rpm && \
    dnf -y install zulu11-jdk && \
    dnf clean all

FROM rockylinux8-nojdk-devtoolset10 AS rockylinux8

RUN dnf -y install https://cdn.azul.com/zulu/bin/zulu-repo-1.0.0-1.noarch.rpm && \
    dnf -y install zulu11-jdk && \
    dnf clean all

FROM rockylinux8-java11-devtoolset10 AS rockylinux8-releaser
# dpkg-source needs a newer GNU tar version that supports --sort=name.
RUN pushd /usr/local/src && \
    curl -fsSL http://ftp.gnu.org/gnu/tar/tar-1.34.tar.bz2 | tar xvj && \
    cd tar-1.34 && \
    FORCE_UNSAFE_CONFIGURE=1 ./configure && \
    make -j && \
    make install && \
    popd && \
    rm -rf /usr/local/src/tar-1.34 && \
    ln -s tar /usr/local/bin/gtar
