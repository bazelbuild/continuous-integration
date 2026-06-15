#!/bin/bash
# This script should run in the root directory of either
# bazelbuild/bazel or bazel-contrib/bazel-docs (or forks thereof).
set -euo pipefail

source "$(dirname "$0")/download_json.sh"

echo "--- Updating Mintlify CLI"
mint version
mint update
mint version

if [[ "$(git config --get remote.origin.url)" == */bazel.git ]]; then
  # Bazel repo -> need to build reference docs and download .json navigation
  echo "--- :bazel::books: Building reference docs"
  echo "Work dir: $(pwd)"

  bazel --quiet build \
    //src/main/java/com/google/devtools/build/lib:gen_mdx_reference_docs

  unzip -q bazel-bin/src/main/java/com/google/devtools/build/lib/mdx-reference-docs.zip -d "$DOCS_DIR"

  cd "$DOCS_DIR"

  echo "--- :json: Downloading docs.json & included files"
  echo "Work dir: $(pwd)"

  # Fetch docs.json and all included files at HEAD, otherwise mintlify fails.
  download_json "$DOCS_JSON_URL"
else
  echo "--- Writing .mintignore"
  echo "upstream/" > .mintignore
fi

echo "+++ :male-detective::books: Checking documentation with Mintlify"

LOG_FILE="log.txt"
# https://www.mintlify.com/docs/installation#validate-documentation-build
# If validation fails, we annotate the build and exit.
# "mint validate" sometimes returns 0 even though parsing errors exist
# (this usually happens if the file is not yet referenced by docs.json).
# That's why we use `script` to print to stdout and a file while preserving
# colored output, then check the file for parsing errors.
if ! script2 -eq "$LOG_FILE" -- "mint validate" || grep -q "parsing error" "$LOG_FILE"; then
  cat /usr/local/annotation.html | buildkite-agent annotate --style "error" --context "mdx_parser"
  exit 1
fi

# TODO: call `mint broken-links`
