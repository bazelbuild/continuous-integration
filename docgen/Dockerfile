# Based on:
# bazelbuild/bazel/scripts/docs/Dockerfile
# bazel-blog/scripts/Dockerfile
# bazelbuild/continuous-integration/buildkite/docker/ubuntu2404/Dockerfile

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND="noninteractive"
ENV LANG="C.UTF-8"
ENV LANGUAGE="C.UTF-8"
ENV LC_ALL="C.UTF-8"

RUN apt-get -qqy update && \
    apt-get -qqy install \
      build-essential \
      curl \
      gnupg2 \
      liblzma-dev \
      python-is-python3 \
      python3 \
      python3-requests \
      python3-yaml \
      ruby \
      ruby-dev \
      unzip \
      zlib1g-dev && \
    apt-get -qqy purge apport && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

### Install Bazelisk.
RUN curl -fLo /usr/local/bin/bazel https://github.com/bazelbuild/bazelisk/releases/download/v1.30.0/bazelisk-linux-amd64 && \
    chown root:root /usr/local/bin/bazel && \
    chmod 0755 /usr/local/bin/bazel
RUN bazel version

### Install Google Cloud CLI.
### https://cloud.google.com/sdk/docs/quickstart-debian-ubuntu
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get update -y && apt-get install google-cloud-cli -y && \
    rm -rf /var/lib/apt/lists/*

COPY Gemfile* .
RUN gem install -g --no-document && rm -f Gemfile*
