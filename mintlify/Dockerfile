# Use the official Node.js LTS image as the base, which includes npm
FROM node:lts-alpine

# Install the mint package globally
RUN npm i -g mint

RUN apk --no-cache add curl jq bash

# Set default environment variables (optional, can be overridden at runtime)
ENV DOCS_DIR="docs"
ENV DOCS_JSON_URL="https://raw.githubusercontent.com/bazel-contrib/bazel-docs/refs/heads/main/docs.json"

COPY --chown=root:root annotation.html /usr/local/annotation.html

COPY --chown=root:root download_json.sh /usr/local/bin/download_json.sh

RUN chmod 0755 /usr/local/bin/download_json.sh

COPY --chown=root:root check_docs.sh /usr/local/bin/check_docs.sh

RUN chmod 0755 /usr/local/bin/check_docs.sh

ENTRYPOINT [ "/bin/bash", "/usr/local/bin/check_docs.sh" ]
