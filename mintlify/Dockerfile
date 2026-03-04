# Use the official Node.js LTS image as the base, which includes npm
FROM node:lts-alpine

# Install the mint package globally
RUN npm i -g mint

RUN apk --no-cache add curl

# Set default environment variable (optional, can be overridden at runtime)
ENV DOCS_DIR="docs"

COPY --chown=root:root check_docs.sh /usr/local/bin/check_docs.sh

RUN chmod 0755 /usr/local/bin/check_docs.sh

ENTRYPOINT [ "/usr/local/bin/check_docs.sh" ]