#!/bin/sh
#
# Builds a release version of the Buildkite Agent from source.
#
# Usage: build-agent.sh <VERSION>
#
set -euo pipefail

version="$1"

workdir="$(mktemp -d)"
trap "rm -rf \"$workdir\"" EXIT

cd "$workdir"

echo "Downloading source-code for Buildkite Agent v${version}..."
git clone --branch "v${version}" --depth=1 "https://github.com/buildkite/agent.git" .

commit="$(git rev-parse HEAD)"
echo "Version v${version} is commit ${commit}."

mkdir pkg
echo "Building Buildkite Agent v${version} for Linux..."
scripts/build-binary.sh linux amd64 "$version"

echo "Building Buildkite Agent v${version} for macOS..."
scripts/build-binary.sh darwin amd64 "$version"

echo "Building Buildkite Agent v${version} for Windows..."
scripts/build-binary.sh windows amd64 "$version"

echo "Uploading release artifacts to GCS..."
gsutil cp pkg/* gs://bazel-buildkite-agent/v${version}-${commit}/

echo "Done! This Buildkite Agent release can be download from:"
for name in pkg/*; do
  echo "   https://storage.googleapis.com/bazel-buildkite-agent/v${version}-${commit}/$(basename $name)"
done
