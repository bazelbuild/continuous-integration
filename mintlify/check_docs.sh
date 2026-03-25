#!/bin/sh
set -euxo pipefail

cd "$DOCS_DIR"

# Fetch the docs.json file at HEAD, otherwise mintlify fails.
curl -sS "$DOCS_JSON_URL" -o docs.json

# https://www.mintlify.com/docs/installation#validate-documentation-build
mint validate

# TODO: call `mint broken-links``
