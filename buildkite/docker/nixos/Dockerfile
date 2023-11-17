FROM nixos/nix

ENV DEBIAN_FRONTEND="noninteractive"
ENV LANG "C.UTF-8"
ENV LANGUAGE "C.UTF-8"
ENV LC_ALL "C.UTF-8"

# Enable Nix Flakes and new commands
RUN echo "experimental-features = nix-command flakes" >> /etc/nix/nix.conf

# Setup nix-ld for prebuilt non-nix binaries (https://github.com/Mic92/nix-ld)
RUN nix profile install \
    nixpkgs#glibc.out \
    nixpkgs#nix-ld \
    nixpkgs#stdenv.cc.cc.lib && \
    mkdir /lib64 && \
    ln -s /nix/var/nix/profiles/default/libexec/nix-ld /lib64/ld-linux-x86-64.so.2
ENV NIX_LD="/nix/var/nix/profiles/default/lib64/ld-linux-x86-64.so.2"
ENV NIX_LD_LIBRARY_PATH="/nix/var/nix/profiles/default/lib"

### Install packages required by Bazel and its tests
RUN nix profile install \
    nixpkgs#bazel-buildtools \
    nixpkgs#bazelisk \
    nixpkgs#coreutils-full \
    nixpkgs#dnsutils \
    nixpkgs#ed \
    nixpkgs#expect \
    nixpkgs#file \
    nixpkgs#gnupg \
    nixpkgs#iproute2 \
    nixpkgs#iputils \
    nixpkgs#lcov \
    nixpkgs#netcat \
    nixpkgs#openssl \
    nixpkgs#python310 \
    nixpkgs#python310Packages.certifi \
    nixpkgs#python310Packages.charset-normalizer \
    nixpkgs#python310Packages.idna \
    nixpkgs#python310Packages.pip \
    nixpkgs#python310Packages.pyyaml \
    nixpkgs#python310Packages.requests \
    nixpkgs#python310Packages.setuptools \
    nixpkgs#python310Packages.six \
    nixpkgs#python310Packages.urllib3 \
    nixpkgs#python310Packages.wheel \
    nixpkgs#sudo \
    nixpkgs#unzip \
    nixpkgs#zip && \
    ln -s /root/.nix-profile/bin/bazelisk /root/.nix-profile/bin/bazel
ENV PYTHONPATH="/root/.nix-profile/lib/python3.10/site-packages"
