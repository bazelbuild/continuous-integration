#!/bin/sh
set -euxo pipefail

cd "$DOCS_DIR"

# Fetch the docs.json file at HEAD, otherwise mintlify fails.
curl -sS "$DOCS_JSON_URL" -o docs.json

# https://www.mintlify.com/docs/installation#validate-documentation-build
# If validation fails, we annotate the build and exit.
if ! mint validate; then
  cat /usr/local/annotation.html | buildkite-agent annotate --style "error" --context "mdx_parser"
  exit 1
fi

# TODO: call `mint broken-links``
