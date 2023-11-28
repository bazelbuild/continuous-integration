FROM ubuntu:22.04

ENV DEBIAN_FRONTEND="noninteractive"
ENV LANG "C.UTF-8"
ENV LANGUAGE "C.UTF-8"
ENV LC_ALL "C.UTF-8"

# Install Nix on Ubuntu and enable Nix Flakes and new commands.
# (https://github.com/odyslam/ddapptools/blob/e255c2dd48222bf82d881e48f58a6000fcb9f1f7/docker/Dockerfile)
# ENV values reverse-engineered from `/root/.nix-profile/etc/profile.d/nix.sh` after Nix is installed, so
# we don't need to worry about every shell `source`ing it.
RUN apt-get update && apt-get install --no-install-recommends -y  locales curl xz-utils vim  ca-certificates && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && mkdir -m 0755 /nix && groupadd -r nixbld && chown root /nix \
    && for n in $(seq 1 10); do useradd -c "Nix build user $n" -d /var/empty -g nixbld -G nixbld -M -N -r -s "$(command -v nologin)" "nixbld$n"; done
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN (curl -L https://nixos.org/nix/install | bash) && \
    mkdir -p /etc/nix && \
    echo "experimental-features = nix-command flakes" >> /etc/nix/nix.conf
ENV USER="root"
ENV NIX_PROFILES="/nix/var/nix/profiles/default /root/.nix-profile"
ENV NIX_SSL_CERT_FILE="/etc/ssl/certs/ca-certificates.crt"
ENV PATH="/root/.nix-profile/bin:$PATH"

### Install packages required by Bazel and its tests.
### All Python dependencies of `bazelci.py`.
### Everything from `defaultShellUtils` (https://github.com/NixOS/nixpkgs/blob/master/pkgs/development/tools/build-managers/bazel/bazel_6/default.nix)
### NOTE 1: Some packages get implicitly pulled in, so conflicts are resolved with `--priority 1` annotations.
### NOTE 2: `bash` is specifically replaced by `bashInteractive` as the former is rarely what's actually wanted.
RUN nix profile install \
    nixpkgs#bashInteractive \
    nixpkgs#bazel-buildtools \
    nixpkgs#bazelisk \
    nixpkgs#coreutils \
    nixpkgs#diffutils \
    nixpkgs#dnsutils \
    nixpkgs#ed \
    nixpkgs#expect \
    nixpkgs#file \
    nixpkgs#findutils \
    nixpkgs#gawk \
    nixpkgs#git --priority 1 \
    nixpkgs#glibc \
    nixpkgs#gnugrep \
    nixpkgs#gnupatch \
    nixpkgs#gnupg \
    nixpkgs#gnused \
    nixpkgs#gnutar \
    nixpkgs#google-cloud-sdk \
    nixpkgs#gzip --priority 1 \
    nixpkgs#iproute2 \
    nixpkgs#iputils \
    nixpkgs#jdk17_headless \
    nixpkgs#lcov \
    nixpkgs#netcat \
    nixpkgs#nix --priority 1 \
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
    nixpkgs#unzip \
    nixpkgs#which --priority 1 \
    nixpkgs#zip \
    nixpkgs#zlib && \
    ln -s /root/.nix-profile/bin/bazelisk /bin/bazel
ENV PYTHONPATH="/root/.nix-profile/lib/python3.10/site-packages"
