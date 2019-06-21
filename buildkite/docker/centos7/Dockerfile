FROM centos:7 as centos7-java8

COPY --from=gcr.io/bazel-public/base:bazelisk /usr/local/bin/bazel /usr/local/bin/bazel
COPY --from=gcr.io/bazel-public/base:buildifier /usr/local/bin/buildifier /usr/local/bin/buildifier
COPY --from=gcr.io/bazel-public/base:github-release /usr/local/bin/github-release /usr/local/bin/github-release
COPY --from=gcr.io/bazel-public/base:saucelabs /usr/local/bin/sc /usr/local/bin/sc

# Ensure that Bazel can use its beloved ISO-8859-1 locale.
RUN localedef -i en_US -f ISO-8859-1 en_US.ISO-8859-1

### Install required packages.
COPY google-cloud-sdk.repo /etc/yum.repos.d/google-cloud-sdk.repo
RUN echo "Enabling EPEL repository..." && \
    yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm && \
    echo "Installing packages required by Bazel..." && \
    yum install -y ed file gcc gcc-c++ git iproute java-1.8.0-openjdk-devel lcov openssl-perl patch python python-six python36 python36-PyYAML python36-six unzip which zip && \
    echo "Installing packages required by Android SDK..." && \
    yum install -y bzip2-libs.i686 ncurses-libs.i686 zlib.i686 && \
    echo "Installing Docker..." && \
    yum install -y yum-utils && \
    yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo && \
    yum install -y containerd.io docker-ce docker-ce-cli && \
    echo "Installing Google Cloud SDK..." && \
    yum install -y google-cloud-sdk && \
    echo "Cleaning up..." && \
    yum clean all

RUN curl -o https://release.bazel.build/0.27.0/release/bazel-0.27.0-centos7-x86_64 /usr/local/bin/bazel && \
    chmod 0755 /usr/local/bin/bazel
