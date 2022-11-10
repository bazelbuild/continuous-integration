FROM centos:7 as centos7
ARG TARGETARCH

# Install required packages.
COPY google-cloud-sdk.repo /etc/yum.repos.d/google-cloud-sdk.repo

# Disable "fastestmirror" plug-in, because it takes a long time.
RUN sed -i 's/enabled=1/enabled=0/' /etc/yum/pluginconf.d/fastestmirror.conf && \
    yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm && \
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

FROM centos7 AS centos7-java8
RUN yum install -y java-1.8.0-openjdk-devel && yum clean all

FROM centos7 AS centos7-java11

# Unfortunately Azul doesn't publish an RPM package for zulu11 on aarch64, so we have to use the tar.gz version.
RUN
RUN mkdir -p /usr/lib/jvm/zulu-11 && \
    pushd /usr/lib/jvm/zulu-11 && \
    if [ "$TARGETARCH" = "arm64" ]; then \
    export DOWNLOAD_URL="https://cdn.azul.com/zulu-embedded/bin/zulu11.58.23-ca-jdk11.0.16.1-linux_aarch64.tar.gz" ; \
    else \
    export DOWNLOAD_URL="https://cdn.azul.com/zulu/bin/zulu11.58.23-ca-jdk11.0.16.1-linux_x64.tar.gz" ; \
    fi; \
    curl "$DOWNLOAD_URL" | tar xvz --strip-components=1 && \
    update-alternatives \
        --install /usr/bin/java java /usr/lib/jvm/zulu-11/bin/java 2115200 \
        --slave /usr/bin/jaotc jaotc /usr/lib/jvm/zulu-11/bin/jaotc \
        --slave /usr/bin/jfr jfr /usr/lib/jvm/zulu-11/bin/jfr \
        --slave /usr/bin/jjs jjs /usr/lib/jvm/zulu-11/bin/jjs \
        --slave /usr/bin/keytool keytool /usr/lib/jvm/zulu-11/bin/keytool \
        --slave /usr/bin/pack200 pack200 /usr/lib/jvm/zulu-11/bin/pack200 \
        --slave /usr/bin/rmid rmid /usr/lib/jvm/zulu-11/bin/rmid \
        --slave /usr/bin/rmiregistry rmiregistry /usr/lib/jvm/zulu-11/bin/rmiregistry \
        --slave /usr/bin/unpack200 unpack200 /usr/lib/jvm/zulu-11/bin/unpack200 \
        --slave /usr/lib/jvm/jre jre /usr/lib/jvm/zulu-11 \
        --slave /usr/share/man/man1/java.1.gz java.1.gz /usr/lib/jvm/zulu-11/man/man1/java.1.gz \
        --slave /usr/share/man/man1/jjs.1.gz jjs.1.gz /usr/lib/jvm/zulu-11/man/man1/jjs.1.gz \
        --slave /usr/share/man/man1/keytool.1.gz keytool.1.gz /usr/lib/jvm/zulu-11/man/man1/keytool.1.gz \
        --slave /usr/share/man/man1/pack200.1.gz pack200.1.gz /usr/lib/jvm/zulu-11/man/man1/pack200.1.gz \
        --slave /usr/share/man/man1/rmid.1.gz rmid.1.gz /usr/lib/jvm/zulu-11/man/man1/rmid.1.gz \
        --slave /usr/share/man/man1/rmiregistry.1.gz rmiregistry.1.gz /usr/lib/jvm/zulu-11/man/man1/rmiregistry.1.gz \
        --slave /usr/share/man/man1/unpack200.1.gz unpack200.1.gz /usr/lib/jvm/zulu-11/man/man1/unpack200.1.gz && \
    update-alternatives \
        --install /usr/bin/javac javac /usr/lib/jvm/zulu-11/bin/javac 2115200 \
        --slave /usr/bin/jar jar /usr/lib/jvm/zulu-11/bin/jar \
        --slave /usr/bin/jarsigner jarsigner /usr/lib/jvm/zulu-11/bin/jarsigner \
        --slave /usr/bin/javadoc javadoc /usr/lib/jvm/zulu-11/bin/javadoc \
        --slave /usr/bin/javap javap /usr/lib/jvm/zulu-11/bin/javap \
        --slave /usr/bin/jcmd jcmd /usr/lib/jvm/zulu-11/bin/jcmd \
        --slave /usr/bin/jconsole jconsole /usr/lib/jvm/zulu-11/bin/jconsole \
        --slave /usr/bin/jdb jdb /usr/lib/jvm/zulu-11/bin/jdb \
        --slave /usr/bin/jdeprscan jdeprscan /usr/lib/jvm/zulu-11/bin/jdeprscan \
        --slave /usr/bin/jdeps jdeps /usr/lib/jvm/zulu-11/bin/jdeps \
        --slave /usr/bin/jhsdb jhsdb /usr/lib/jvm/zulu-11/bin/jhsdb \
        --slave /usr/bin/jimage jimage /usr/lib/jvm/zulu-11/bin/jimage \
        --slave /usr/bin/jinfo jinfo /usr/lib/jvm/zulu-11/bin/jinfo \
        --slave /usr/bin/jlink jlink /usr/lib/jvm/zulu-11/bin/jlink \
        --slave /usr/bin/jmap jmap /usr/lib/jvm/zulu-11/bin/jmap \
        --slave /usr/bin/jmod jmod /usr/lib/jvm/zulu-11/bin/jmod \
        --slave /usr/bin/jps jps /usr/lib/jvm/zulu-11/bin/jps \
        --slave /usr/bin/jrunscript jrunscript /usr/lib/jvm/zulu-11/bin/jrunscript \
        --slave /usr/bin/jshell jshell /usr/lib/jvm/zulu-11/bin/jshell \
        --slave /usr/bin/jstack jstack /usr/lib/jvm/zulu-11/bin/jstack \
        --slave /usr/bin/jstat jstat /usr/lib/jvm/zulu-11/bin/jstat \
        --slave /usr/bin/jstatd jstatd /usr/lib/jvm/zulu-11/bin/jstatd \
        --slave /usr/bin/rmic rmic /usr/lib/jvm/zulu-11/bin/rmic \
        --slave /usr/bin/serialver serialver /usr/lib/jvm/zulu-11/bin/serialver \
        --slave /usr/share/man/man1/javac.1.gz javac.1.gz /usr/lib/jvm/zulu-11/man/man1/javac.1.gz \
        --slave /usr/share/man/man1/jar.1.gz jar.1.gz /usr/lib/jvm/zulu-11/man/man1/jar.1.gz \
        --slave /usr/share/man/man1/jarsigner.1.gz jarsigner.1.gz /usr/lib/jvm/zulu-11/man/man1/jarsigner.1.gz \
        --slave /usr/share/man/man1/javadoc.1.gz javadoc.1.gz /usr/lib/jvm/zulu-11/man/man1/javadoc.1.gz \
        --slave /usr/share/man/man1/javap.1.gz javap.1.gz /usr/lib/jvm/zulu-11/man/man1/javap.1.gz \
        --slave /usr/share/man/man1/jcmd.1.gz jcmd.1.gz /usr/lib/jvm/zulu-11/man/man1/jcmd.1.gz \
        --slave /usr/share/man/man1/jconsole.1.gz jconsole.1.gz /usr/lib/jvm/zulu-11/man/man1/jconsole.1.gz \
        --slave /usr/share/man/man1/jdb.1.gz jdb.1.gz /usr/lib/jvm/zulu-11/man/man1/jdb.1.gz \
        --slave /usr/share/man/man1/jdeps.1.gz jdeps.1.gz /usr/lib/jvm/zulu-11/man/man1/jdeps.1.gz \
        --slave /usr/share/man/man1/jinfo.1.gz jinfo.1.gz /usr/lib/jvm/zulu-11/man/man1/jinfo.1.gz \
        --slave /usr/share/man/man1/jmap.1.gz jmap.1.gz /usr/lib/jvm/zulu-11/man/man1/jmap.1.gz \
        --slave /usr/share/man/man1/jps.1.gz jps.1.gz /usr/lib/jvm/zulu-11/man/man1/jps.1.gz \
        --slave /usr/share/man/man1/jrunscript.1.gz jrunscript.1.gz /usr/lib/jvm/zulu-11/man/man1/jrunscript.1.gz \
        --slave /usr/share/man/man1/jstack.1.gz jstack.1.gz /usr/lib/jvm/zulu-11/man/man1/jstack.1.gz \
        --slave /usr/share/man/man1/jstat.1.gz jstat.1.gz /usr/lib/jvm/zulu-11/man/man1/jstat.1.gz \
        --slave /usr/share/man/man1/jstatd.1.gz jstatd.1.gz /usr/lib/jvm/zulu-11/man/man1/jstatd.1.gz \
        --slave /usr/share/man/man1/rmic.1.gz rmic.1.gz /usr/lib/jvm/zulu-11/man/man1/rmic.1.gz \
        --slave /usr/share/man/man1/serialver.1.gz serialver.1.gz /usr/lib/jvm/zulu-11/man/man1/serialver.1.gz && \
    popd && \
    java -version && \
    javac -version

FROM centos7-java11 AS centos7-java11-devtoolset10
RUN yum install -y centos-release-scl && yum install -y devtoolset-10 && yum clean all

# These are the variables set by /opt/rh/devtoolset-10/enable and necessary to activate devtoolset-10.
ENV PATH=/opt/rh/devtoolset-10/root/usr/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV MANPATH=/opt/rh/devtoolset-10/root/usr/share/man
ENV INFOPATH=/opt/rh/devtoolset-10/root/usr/share/info
ENV PCP_DIR=/opt/rh/devtoolset-10/root
ENV LD_LIBRARY_PATH=/opt/rh/devtoolset-10/root/usr/lib64:/opt/rh/devtoolset-10/root/usr/lib:/opt/rh/devtoolset-10/root/usr/lib64/dyninst:/opt/rh/devtoolset-10/root/usr/lib/dyninst:/opt/rh/devtoolset-10/root/usr/lib64:/opt/rh/devtoolset-10/root/usr/lib
ENV PKG_CONFIG_PATH=/opt/rh/devtoolset-10/root/usr/lib64/pkgconfig

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
