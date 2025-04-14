FROM centos:7 AS centos7-nojdk
ARG TARGETARCH

# Install required packages.
COPY google-cloud-sdk.repo /etc/yum.repos.d/google-cloud-sdk.repo

# Disable "fastestmirror" plug-in, because it takes a long time.
# TODO: https://archives.fedoraproject.org/pub/archive/epel/7/aarch64/Packages/e/epel-release-7-12.noarch.rpm
RUN sed -i 's/enabled=1/enabled=0/' /etc/yum/pluginconf.d/fastestmirror.conf &&
    # CentOS 7 has been deprecated, so rewrite URLs to point to vault
    sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-* &&
    sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-* &&
    yum install -y https://archives.fedoraproject.org/pub/archive/epel/7/x86_64/Packages/e/epel-release-7-14.noarch.rpm && \
    yum install -y \
    bind-utils \
    dpkg-dev \
    ed \
    file \
    gcc \
    gcc-c++ \
    git \
    gnupg2 \
    google-cloud-sdk \
    iproute \
    lcov \
    openssl-perl \
    patch \
    python \
    python-six \
    python36 \
    python36-PyYAML \
    python36-requests \
    python36-six \
    rpm-build \
    sudo \
    unzip \
    which \
    zip \
    && \
    yum clean all

# Allow using sudo inside the container.
RUN echo "ALL ALL=(ALL:ALL) NOPASSWD: ALL" >> /etc/sudoers

RUN yum install -y yum-utils && \
    yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo && \
    yum install -y containerd.io docker-ce docker-ce-cli && \
    yum clean all

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

FROM centos7-nojdk AS centos7-nojdk-devtoolset10

RUN yum install -y centos-release-scl && yum install -y devtoolset-10 && yum clean all

# These are the variables set by /opt/rh/devtoolset-10/enable and necessary to activate devtoolset-10.
ENV PATH=/opt/rh/devtoolset-10/root/usr/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV MANPATH=/opt/rh/devtoolset-10/root/usr/share/man
ENV INFOPATH=/opt/rh/devtoolset-10/root/usr/share/info
ENV PCP_DIR=/opt/rh/devtoolset-10/root
ENV LD_LIBRARY_PATH=/opt/rh/devtoolset-10/root/usr/lib64:/opt/rh/devtoolset-10/root/usr/lib:/opt/rh/devtoolset-10/root/usr/lib64/dyninst:/opt/rh/devtoolset-10/root/usr/lib/dyninst:/opt/rh/devtoolset-10/root/usr/lib64:/opt/rh/devtoolset-10/root/usr/lib
ENV PKG_CONFIG_PATH=/opt/rh/devtoolset-10/root/usr/lib64/pkgconfig

FROM centos7-nojdk AS centos7-java8

RUN yum install -y java-1.8.0-openjdk-devel && yum clean all

FROM centos7-nojdk AS centos7-java11

RUN yum install -y https://cdn.azul.com/zulu/bin/zulu-repo-1.0.0-1.noarch.rpm && \
    yum install -y yum install zulu11-jdk && yum clean all

FROM centos7-nojdk-devtoolset10 AS centos7-java11-devtoolset10

RUN yum install -y https://cdn.azul.com/zulu/bin/zulu-repo-1.0.0-1.noarch.rpm && \
    yum install -y yum install zulu11-jdk && yum clean all

FROM centos7-nojdk-devtoolset10 AS centos7

RUN yum install -y https://cdn.azul.com/zulu/bin/zulu-repo-1.0.0-1.noarch.rpm && \
    yum install -y yum install zulu21-jdk && yum clean all

FROM centos7-java11-devtoolset10 AS centos7-releaser
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
