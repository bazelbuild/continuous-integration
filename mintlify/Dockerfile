# This Dockerfile is way more complex than it should be thanks to a bug in the
# Mintlify CLI: It does not fail when it discovers parsing errors in .mdx
# files that are not (yet) referenced by docs.json.
# We work around this issue by running mint via script(1) - unlike tee(1) it
# is able to redirect output to a file while preserving colored output in the
# terminal. Then we check the file contents for actual parsing errors.
# Unfortunately the newest readily available version of script is too old,
# so we need to build our own binary (called script2) in the build stage.

# Build stage
FROM gcr.io/bazel-public/ubuntu2404 AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    tar \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Download, extract, and build util-linux
RUN wget -c "https://www.kernel.org/pub/linux/utils/util-linux/v2.42/util-linux-2.42.1.tar.gz" -O util-linux.tar.gz \
    && tar -xzvf util-linux.tar.gz \
    && cd util-linux-2.42.1 \
    && ./configure --disable-all-programs --enable-scriptutils \
    && make

# Use the Bazel public image as the base
FROM gcr.io/bazel-public/ubuntu2404

# Install dependencies: jq and deps of nodejs
RUN apt-get update && apt-get install -y \
    jq ca-certificates curl gnupg

# Copy the compiled binary from the builder stage
COPY --from=builder /build/util-linux-2.42.1/script /usr/bin/script2

# Ensure it's executable
RUN chmod +x /usr/bin/script2

# Install nodejs as per https://github.com/nodesource/distributions/wiki/Repository-Manual-Installation#debian-systems
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_24.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs

# Install the mint package
WORKDIR /usr/local/lib/mintlify
COPY package.json package-lock.json ./
RUN npm ci && npm cache clean --force
ENV PATH="/usr/local/lib/mintlify/node_modules/.bin:${PATH}"

WORKDIR /

# Set default environment variables (optional, can be overridden at runtime)
ENV DOCS_DIR="docs"
ENV DOCS_JSON_URL="https://raw.githubusercontent.com/bazel-contrib/bazel-docs/refs/heads/main/docs.json"

COPY --chown=root:root annotation.html /usr/local/annotation.html

COPY --chown=root:root download_json.sh /usr/local/bin/download_json.sh

RUN chmod 0755 /usr/local/bin/download_json.sh

COPY --chown=root:root check_docs.sh /usr/local/bin/check_docs.sh

RUN chmod 0755 /usr/local/bin/check_docs.sh

ENTRYPOINT [ "/bin/bash", "/usr/local/bin/check_docs.sh" ]
