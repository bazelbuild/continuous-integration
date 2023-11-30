FROM ubuntu:22.04

ENV DEBIAN_FRONTEND="noninteractive"
ENV LANG "C.UTF-8"
ENV LANGUAGE "C.UTF-8"
ENV LC_ALL "C.UTF-8"

# Install Nix on Ubuntu and enable Nix Flakes and new commands.
# (https://github.com/odyslam/ddapptools/blob/e255c2dd48222bf82d881e48f58a6000fcb9f1f7/docker/Dockerfile)
# ENV values expose the default (aka `root`'s) Nix profile so that the tools installed below are always
# available without needing to `source ~/.nix-profile/etc/profile.d/nix.sh` in every shell.
# An ENTRYPOINT script is needed to start `nix daemon` so that non-root users can actually use Nix.
# Sudo is set up to allow any commands, include Nix on `PATH`, and specifically whitelists the ENTRYPOINT script.
RUN apt-get update && apt-get install --no-install-recommends -y locales curl xz-utils vim ca-certificates sudo && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && mkdir -m 0755 /nix && groupadd --gid 30000 nixbld && chown root /nix \
    && for n in $(seq 1 10); do useradd --comment "Nix build user $n" --home-dir /var/empty --gid nixbld --groups nixbld --no-create-home --no-user-group --uid $((30000 + $n)) --shell "$(command -v nologin)" "nixbld$n"; done
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN (curl -L https://nixos.org/nix/install | bash) && \
    mkdir -p /etc/nix && \
    echo "experimental-features = nix-command flakes" >> /etc/nix/nix.conf && \
    echo $'#!/bin/bash\nsudo daemon --unsafe nix daemon\nexec "$@"' > /entrypoint.sh && \
    chmod 0777 /entrypoint.sh && \
    echo "Defaults    secure_path = /nix/var/nix/profiles/default/bin:$PATH" >> /etc/sudoers && \
    echo "ALL ALL=(ALL:ALL) NOPASSWD:ALL,/entrypoint.sh" >> /etc/sudoers
ENV NIX_PROFILES="/nix/var/nix/profiles/default"
ENV NIX_SSL_CERT_FILE="/etc/ssl/certs/ca-certificates.crt"
ENV NIX_REMOTE="daemon"
ENV PATH="/nix/var/nix/profiles/default/bin:$PATH"
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]

### Install packages required by Bazel and its tests.
### All Python dependencies of `bazelci.py`.
### Everything from `defaultShellUtils` (https://github.com/NixOS/nixpkgs/blob/master/pkgs/development/tools/build-managers/bazel/bazel_6/default.nix)
### NOTE 1: `NIX_REMOTE` is explicit unset as `nix daemon` isn't running during the `RUN` step.
### NOTE 2: Some packages get implicitly pulled in, so conflicts are resolved with `--priority 1` annotations.
### NOTE 3: `bash` is specifically replaced by `bashInteractive` as the former is rarely what's actually wanted.
RUN unset NIX_REMOTE && nix profile install \
    nixpkgs#bashInteractive \
    nixpkgs#bazel-buildtools \
    nixpkgs#bazelisk \
    nixpkgs#coreutils \
    nixpkgs#daemon \
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
    nixpkgs#nano \
    nixpkgs#iproute2 \
    nixpkgs#iputils \
    nixpkgs#jdk17_headless \
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
    nixpkgs#unzip \
    nixpkgs#which --priority 1 \
    nixpkgs#zip \
    nixpkgs#zlib && \
    ln -s /nix/var/nix/profiles/default/bin/bazelisk /bin/bazel
ENV PYTHONPATH="/nix/var/nix/profiles/default/lib/python3.10/site-packages"
