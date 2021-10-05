FROM quay.io/pypa/manylinux2014_x86_64:latest as manylinux2014
ARG BUILDARCH

# Install required packages.
COPY google-cloud-sdk.repo /etc/yum.repos.d/google-cloud-sdk.repo

# Activate Python 3.9.
RUN ln -sv /opt/python/cp39-cp39/bin/{pip3,python3} /usr/local/bin && \
    pip3 install requests PyYAML

# Disable "fastestmirror" plug-in, because it takes a long time.
RUN sed -i 's/enabled=1/enabled=0/' /etc/yum/pluginconf.d/fastestmirror.conf && \
    yum install -y \
    java-11-openjdk-devel \
    zip \
    && \
    yum clean all

# Allow using sudo inside the container.
RUN echo "ALL ALL=(ALL:ALL) NOPASSWD: ALL" >> /etc/sudoers

# Ensure that Bazel can use its beloved ISO-8859-1 locale.
RUN localedef -i en_US -f ISO-8859-1 en_US.ISO-8859-1

# gsutil
RUN curl -fsSL https://storage.googleapis.com/pub/gsutil.tar.gz | tar xfz - -C /opt && \
    ln -s /opt/gsutil/gsutil /usr/bin/gsutil

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
