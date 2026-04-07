# Use the Bazel public image as the base
FROM gcr.io/bazel-public/ubuntu2404

# Install dependencies: jq and deps of nodejs
RUN apt-get update && apt-get install -y \
    jq ca-certificates curl gnupg

# Install nodejs as per https://github.com/nodesource/distributions/wiki/Repository-Manual-Installation#debian-systems
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_24.x nodistro main" | sudo tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs

# Install the mint package globally
RUN npm i -g mint

# Set default environment variables (optional, can be overridden at runtime)
ENV DOCS_DIR="docs"
ENV DOCS_JSON_URL="https://raw.githubusercontent.com/bazel-contrib/bazel-docs/refs/heads/main/docs.json"

COPY --chown=root:root annotation.html /usr/local/annotation.html

COPY --chown=root:root download_json.sh /usr/local/bin/download_json.sh

RUN chmod 0755 /usr/local/bin/download_json.sh

COPY --chown=root:root check_docs.sh /usr/local/bin/check_docs.sh

RUN chmod 0755 /usr/local/bin/check_docs.sh

ENTRYPOINT [ "/bin/bash", "/usr/local/bin/check_docs.sh" ]
