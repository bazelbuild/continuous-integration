#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/download_json.sh"

cd "$DOCS_DIR"

echo "--- :json: Downloading docs.json & included files"

# Fetch docs.json and all included files at HEAD, otherwise mintlify fails.
download_json "$DOCS_JSON_URL"

echo "+++ :male-detective::books: Checking documentation with Mintlify"

# https://www.mintlify.com/docs/installation#validate-documentation-build
# If validation fails, we annotate the build and exit.
if ! mint validate; then
  cat /usr/local/annotation.html | buildkite-agent annotate --style "error" --context "mdx_parser"
  exit 1
fi

# TODO: call `mint broken-links`
