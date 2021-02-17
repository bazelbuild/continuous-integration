# Based on:
# bazelbuild/bazel/scripts/docs/Dockerfile
# bazel-blog/scripts/Dockerfile
# bazelbuild/continuous-integration/buildkite/docker/ubuntu1804/Dockerfile

FROM ubuntu:18.04

ENV DEBIAN_FRONTEND="noninteractive"
RUN apt-get -qqy update && \
    apt-get -qqy install build-essential curl liblzma-dev \
      python3.7 python-pygments ruby ruby-dev unzip zlib1g-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN ln -fs /usr/bin/python3.7 /usr/bin/python

### Install packages required by bazelci.pys
RUN dpkg --add-architecture i386 && \
    apt-get -qqy update && \
    apt-get -qqy install --no-install-recommends \
    python3-requests \
    python3-yaml \
    && \
    apt-get -qqy purge apport && \
    rm -rf /var/lib/apt/lists/*

### Install Bazelisk.
RUN curl -fLo /usr/local/bin/bazel https://github.com/bazelbuild/bazelisk/releases/download/v1.7.5/bazelisk-linux-amd64 && \
    chown root:root /usr/local/bin/bazel && \
    chmod 0755 /usr/local/bin/bazel
RUN bazel version

### Install Google Cloud SDK.
### https://cloud.google.com/sdk/docs/quickstart-debian-ubuntu
RUN export CLOUD_SDK_REPO="cloud-sdk-bionic" && \
    echo "deb http://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl -L https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
    apt-get -qqy update && \
    apt-get -qqy install google-cloud-sdk && \
    rm -rf /var/lib/apt/lists/*

COPY Gemfile .
RUN gem install -g --no-rdoc --no-ri && rm -f Gemfile