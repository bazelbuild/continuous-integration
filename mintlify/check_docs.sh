#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/download_json.sh"

echo "--- :bazel::books: Building reference docs"

bazel --quiet build \
  //src/main/java/com/google/devtools/build/lib:gen_mdx_reference_docs

unzip -q bazel-bin/src/main/java/com/google/devtools/build/lib/mdx-reference-docs.zip -d "$DOCS_DIR"

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
