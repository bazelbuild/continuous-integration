#!/bin/sh
set -euxo pipefail

cd "$DOCS_DIR"

# https://www.mintlify.com/docs/installation#validate-documentation-build
mint validate
