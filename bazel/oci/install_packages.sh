#!/bin/bash

set -o errexit -o nounset -o pipefail

apt-get update

export DEBIAN_FRONTEND="noninteractive"
export TZ="Etc/UTC"

apt-get install --yes \
    build-essential \
    curl \
    git \
    openjdk-8-jdk \
    python3 \
    python3-pip \
    unzip \
    zip

ln -s "$(which python3)" /usr/bin/python
